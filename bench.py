"""Run a reproducible retrieval benchmark over the tuition-fee corpus.

Usage (from the project root)::

    python bench.py
    python bench.py --strategy fixed --chunk-size 600

The script deliberately does retrieval only.  Its output shows the evidence
chunks that an agent should use before comparing an eventual answer with the
gold answer.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker
from src.embeddings import _mock_embed
from src.models import Document
from src.store import EmbeddingStore


DEFAULT_DATA_DIR = Path("data/hocbong_hocphi")
DEFAULT_OUTPUT = Path("ket_qua_benchmark.txt")
DEFAULT_BENCHMARK_FILE = Path("benchmark.jsonl")


@dataclass(frozen=True)
class BenchmarkCase:
    """One question whose answer was checked against a source Markdown file."""

    question: str
    gold_answer: str
    gold_doc_ids: tuple[str, ...]
    required_terms: tuple[str, ...]
    metadata_filter: dict[str, str] | None = None


# These gold answers are stated in the corresponding source files.  They are
# intentionally diverse: numeric fact, deadline, payment process, refund, and
# an eligibility/rule question.
BENCHMARKS = (
    BenchmarkCase(
        question="Học phí hệ đại trà của NEU năm học 2026-2027 cho khóa 65, 66 và 67 là bao nhiêu mỗi tín chỉ?",
        gold_answer="770.000 đồng/tín chỉ.",
        gold_doc_ids=("neu-tuition-decision-985-2026-2027",),
        required_terms=("770.000", "Khóa 65, 66, 67"),
    ),
    BenchmarkCase(
        question="Sinh viên UET trong danh sách chưa hoàn thành học phí được gia hạn nộp đến ngày nào vào tháng 5/2026?",
        gold_answer="Đến hết ngày 26/5/2026.",
        gold_doc_ids=("uet-tuition-payment-extension-2025-2026",),
        required_terms=("26/5/2026", "gia hạn"),
    ),
    BenchmarkCase(
        question="USTH hướng dẫn sinh viên nộp học phí học kỳ II năm học 2025-2026 bằng hình thức nào?",
        gold_answer="Chuyển khoản qua mã QR hiển thị trên hệ thống ERP của Nhà trường.",
        gold_doc_ids=("usth-tuition-semester-2-2025-2026",),
        required_terms=("mã QR", "hệ thống ERP"),
    ),
    BenchmarkCase(
        question="Tiền hoàn trả học phí của sinh viên UET được chuyển vào đâu?",
        gold_answer="Vào tài khoản cá nhân của sinh viên.",
        gold_doc_ids=("uet-tuition-refund-2026-03",),
        required_terms=("tài khoản cá nhân", "hoàn trả học phí"),
        # This is deliberately evaluated both without and with the filter so
        # the report can demonstrate metadata pre-filtering.
        metadata_filter={"audience": "student"},
    ),
    BenchmarkCase(
        question="Bách khoa Hà Nội tính học phí của sinh viên theo cơ sở nào ở mỗi học kỳ?",
        gold_answer="Theo số tín chỉ học phí của các học phần sinh viên đăng ký học ở mỗi học kỳ.",
        gold_doc_ids=("hust-tuition-2024-2025",),
        required_terms=("số tín chỉ học phí", "mỗi học kỳ"),
    ),
)


class TfidfEmbedder:
    """Small dependency-free lexical embedder fitted on the current corpus.

    Unlike the classroom ``_mock_embed`` fallback, this vector represents
    words and adjacent word pairs actually present in the Vietnamese corpus.
    It is a transparent baseline when a semantic model/API is unavailable.
    """

    STOP_WORDS = {
        "và", "là", "của", "có", "cho", "các", "được", "trong", "với", "tại", "về",
        "một", "những", "này", "theo", "đến", "từ", "khi", "đã", "sẽ", "do", "để",
        "năm", "học", "sinh", "viên", "trường", "đại", "thông", "báo", "hệ", "chương",
    }

    def __init__(self, texts: list[str]) -> None:
        document_features = [set(self._features(text)) for text in texts]
        document_frequency = Counter(feature for features in document_features for feature in features)
        self.vocabulary = {feature: index for index, feature in enumerate(sorted(document_frequency))}
        document_count = max(1, len(texts))
        self.idf = {
            feature: math.log((document_count + 1) / (frequency + 1)) + 1.0
            for feature, frequency in document_frequency.items()
        }

    @classmethod
    def _features(cls, text: str) -> list[str]:
        tokens = [
            token.casefold()
            for token in re.findall(r"\d+(?:[.,/]\d+)*|[^\W_]+", text)
            if token.casefold() not in cls.STOP_WORDS and len(token) > 1
        ]
        # Bigrams distinguish phrases such as "kỹ thuật phần mềm" from a
        # page that happens to contain only one of those common words.
        bigrams = [f"{left} {right}" for left, right in zip(tokens, tokens[1:])]
        return tokens + bigrams

    def __call__(self, text: str) -> list[float]:
        vector = [0.0] * len(self.vocabulary)
        features = self._features(text)
        if not features:
            return vector
        counts = Counter(features)
        for feature, count in counts.items():
            index = self.vocabulary.get(feature)
            if index is not None:
                vector[index] = (count / len(features)) * self.idf[feature]
        magnitude = math.sqrt(sum(value * value for value in vector))
        return [value / magnitude for value in vector] if magnitude else vector


def make_embedding(backend: str, chunks: list[Document]):
    """Build the selected embedding function after all chunks are available."""
    if backend == "mock":
        return _mock_embed, "mock (MD5 pseudo-random; chỉ dùng để test code)"
    return TfidfEmbedder([chunk.content for chunk in chunks]), "TF-IDF unigram + bigram (lexical baseline)"


def load_benchmarks(path: Path | None) -> tuple[BenchmarkCase, ...]:
    """Load the group-agreed JSONL questions, or use the built-in fallback."""
    if path is None or not path.is_file():
        return BENCHMARKS

    cases: list[BenchmarkCase] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            item = json.loads(line)
            gold_doc_ids = tuple(item.get("gold_doc_ids", ()))
            if not item.get("question") or not item.get("gold_answer") or not gold_doc_ids:
                raise ValueError(f"{path}:{line_number} thiếu question, gold_answer hoặc gold_doc_ids.")
            cases.append(
                BenchmarkCase(
                    question=item["question"],
                    gold_answer=item["gold_answer"],
                    gold_doc_ids=gold_doc_ids,
                    required_terms=tuple(item.get("gold_evidence", ())),
                    # q1 is intentionally broad; the student-only notice is
                    # the relevant audience, so this produces the required
                    # unfiltered-versus-filtered A/B comparison.
                    metadata_filter={"audience": "student"} if item.get("id") == "q1" else None,
                )
            )
    if len(cases) != 5:
        raise ValueError(f"{path} phải có đúng 5 benchmark queries, hiện có {len(cases)}.")
    return tuple(cases)


def parse_frontmatter(markdown: str) -> tuple[dict[str, str], str]:
    """Return simple YAML frontmatter metadata and the Markdown body.

    The corpus uses flat ``key: value`` frontmatter, so a small dependency-free
    parser is preferable to requiring PyYAML for a lab utility.
    """
    if not markdown.startswith("---"):
        return {}, markdown.strip()

    parts = markdown.split("---", 2)
    if len(parts) < 3:
        return {}, markdown.strip()

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        metadata[key] = value
    return metadata, parts[2].strip()


def make_chunker(strategy: str, chunk_size: int):
    """Create exactly one switchable chunking strategy for fair comparison."""
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=chunk_size, overlap=min(80, chunk_size - 1))
    if strategy == "sentence":
        return SentenceChunker(max_sentences_per_chunk=3)
    return RecursiveChunker(chunk_size=chunk_size)


def load_chunks(data_dir: Path, chunker: Any) -> tuple[list[Document], list[str]]:
    """Load Markdown files and turn each body chunk into a Document."""
    documents: list[Document] = []
    warnings: list[str] = []
    for path in sorted(data_dir.glob("*.md")):
        metadata, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        doc_id = metadata.get("doc_id", path.stem)
        if not body:
            warnings.append(f"Bỏ qua {path.name}: không có phần body.")
            continue

        chunks = chunker.chunk(body)
        if not chunks:
            warnings.append(f"Bỏ qua {path.name}: chunker không tạo chunk nào.")
            continue

        for index, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata,
                "doc_id": doc_id,
                "chunk_index": str(index),
                "source_file": path.name,
            }
            documents.append(
                Document(id=f"{doc_id}#{index}", content=chunk, metadata=chunk_metadata)
            )
    return documents, warnings


def excerpt(text: str, limit: int = 260) -> str:
    """One-line preview that keeps the output file easy to scan."""
    compact = " ".join(text.split())
    return compact if len(compact) <= limit else f"{compact[:limit - 3]}..."


def evaluate(results: list[dict[str, Any]], case: BenchmarkCase) -> tuple[bool, bool]:
    """Check source-document presence and at least one visible gold span."""
    has_gold_doc = any(item["metadata"].get("doc_id") in case.gold_doc_ids for item in results)
    combined = " ".join(item["content"] for item in results).casefold()
    # A multi-part answer can legitimately be spread over more than one chunk
    # and crawled tables can lose whitespace.  For retrieval evaluation, one
    # original gold-evidence span plus the correct source is meaningful; the
    # final agent answer is still checked separately against the full gold.
    has_evidence = any(term.casefold() in combined for term in case.required_terms)
    return has_gold_doc, has_evidence


def format_results(label: str, results: list[dict[str, Any]], case: BenchmarkCase) -> list[str]:
    """Render top-k results and lightweight evidence checks."""
    found_doc, found_terms = evaluate(results, case)
    lines = [
        f"  {label}",
        f"  Gold document in top-3: {'YES' if found_doc else 'NO'} | "
        f"Ít nhất một gold-evidence span trong top-3: {'YES' if found_terms else 'NO'}",
    ]
    if not results:
        return lines + ["    (Không có kết quả)"]

    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        lines.extend(
            [
                f"    #{rank} score={result['score']:.4f} doc_id={metadata.get('doc_id', 'N/A')} "
                f"chunk={metadata.get('chunk_index', 'N/A')}",
                f"       audience={metadata.get('audience', 'N/A')} | title={metadata.get('title', 'N/A')}",
                f"       {excerpt(result['content'])}",
            ]
        )
    return lines


def run_benchmark(
    data_dir: Path,
    output_path: Path,
    strategy: str,
    chunk_size: int,
    top_k: int,
    benchmark_file: Path | None = DEFAULT_BENCHMARK_FILE,
    embedding_backend: str = "tfidf",
) -> str:
    """Index the corpus, run all five cases, save and return the report."""
    if not data_dir.is_dir():
        raise FileNotFoundError(f"Không tìm thấy thư mục corpus: {data_dir}")

    chunker = make_chunker(strategy, chunk_size)
    chunks, warnings = load_chunks(data_dir, chunker)
    if not chunks:
        raise RuntimeError("Corpus không tạo được chunk nào để benchmark.")

    embedding_fn, embedding_label = make_embedding(embedding_backend, chunks)
    store = EmbeddingStore(collection_name="tuition_benchmark", embedding_fn=embedding_fn)
    store.add_documents(chunks)
    benchmarks = load_benchmarks(benchmark_file)

    source_docs = len({chunk.metadata["doc_id"] for chunk in chunks})
    lines = [
        "BENCHMARK RETRIEVAL — HỌC PHÍ ĐẠI HỌC",
        f"Corpus: {data_dir}",
        f"Chiến lược chunking: {strategy} | chunk_size: {chunk_size}",
        f"Embedding: {embedding_label}",
        f"Tài liệu nguồn: {source_docs} | Chunks đã nạp: {store.get_collection_size()}",
        f"Bộ câu hỏi: {benchmark_file if benchmark_file and benchmark_file.is_file() else 'mặc định trong bench.py'}",
        "Lưu ý: score chỉ dùng để xếp hạng; luôn đọc excerpt và đối chiếu gold evidence.",
    ]
    if warnings:
        lines.extend(["Cảnh báo:", *[f"- {warning}" for warning in warnings]])

    for number, case in enumerate(benchmarks, start=1):
        lines.extend(
            [
                "",
                f"QUERY {number}: {case.question}",
                f"Gold answer: {case.gold_answer}",
                f"Nguồn kiểm chứng: {', '.join(f'{doc_id}.md' for doc_id in case.gold_doc_ids)}",
            ]
        )

        unfiltered = store.search_with_filter(case.question, top_k=top_k)
        lines.extend(format_results("A. Không lọc metadata (top-3):", unfiltered, case))

        if case.metadata_filter:
            filtered = store.search_with_filter(
                case.question, top_k=top_k, metadata_filter=case.metadata_filter
            )
            lines.append(f"  B. Có lọc metadata {case.metadata_filter} (top-3):")
            # Avoid repeating a nested label in the A/B section.
            rendered = format_results("Kết quả lọc:", filtered, case)
            lines.extend(rendered[1:])

    report = "\n".join(lines) + "\n"
    output_path.write_text(report, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark retrieval cho corpus Markdown học phí.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--strategy", choices=("fixed", "sentence", "recursive"), default="recursive")
    parser.add_argument("--chunk-size", type=int, default=700)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--embedding",
        choices=("tfidf", "mock"),
        default="tfidf",
        help="TF-IDF là baseline lexical thực; mock chỉ dùng để kiểm thử cấu trúc.",
    )
    parser.add_argument(
        "--benchmark-file",
        type=Path,
        default=DEFAULT_BENCHMARK_FILE,
        help="JSONL gồm đúng 5 câu hỏi nhóm; nếu file không tồn tại sẽ dùng bộ mặc định.",
    )
    args = parser.parse_args()

    if args.chunk_size < 1 or args.top_k < 1:
        parser.error("--chunk-size và --top-k phải lớn hơn 0.")

    report = run_benchmark(
        args.data_dir,
        args.output,
        args.strategy,
        args.chunk_size,
        args.top_k,
        args.benchmark_file,
        args.embedding,
    )
    # Some Windows terminals still start Python with a legacy code page.
    # Reconfigure only the terminal stream; the saved report is UTF-8 already.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(report, end="")
    print(f"Đã lưu kết quả: {args.output}")


if __name__ == "__main__":
    main()
