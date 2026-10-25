"""Restore and validate the frozen release index without a DVC remote."""

import argparse
import hashlib
import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np

from civil_code_rag.config import PROJECT_ROOT, Settings

MODEL_NAME = "intfloat/multilingual-e5-small"
MODEL_REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_records(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text("utf-8").splitlines()
        if line.strip()
    ]


def validate_index(index_dir: Path, corpus_path: Path) -> dict:
    """Check alignment, language, source IDs, dimensions and finite unit vectors."""
    corpus = read_records(corpus_path)
    records = read_records(index_dir / "index_records.jsonl")
    vectors = np.load(index_dir / "embeddings.npy", allow_pickle=False)
    if vectors.ndim != 2 or len(vectors) != len(records) or not records:
        raise ValueError("Invalid vector/record alignment.")
    if not np.isfinite(vectors).all():
        raise ValueError("Non-finite vectors.")
    if not np.allclose(np.linalg.norm(vectors, axis=1), 1.0, atol=1e-5):
        raise ValueError("Index vectors must be normalized.")
    ids = {r["article_id"] for r in corpus}
    record_ids = [r["record_id"] for r in records]
    if len(ids) != len(corpus) or len(set(record_ids)) != len(records):
        raise ValueError("Duplicate IDs.")
    if any(
        r["article_id"] not in ids or r["language"] not in {"ar", "en"} for r in records
    ):
        raise ValueError("Index sources are not aligned with the corpus.")
    return {
        "status": "ok",
        "indexed_document_count": len(records),
        "corpus_record_count": len(corpus),
    }


def inspect_health(settings: Settings) -> dict:
    """Check local data without loading embeddings models or contacting OpenAI."""
    return validate_index(settings.index_dir, settings.corpus_path)


def restore(output: Path, root: Path = PROJECT_ROOT) -> dict:
    """Extract only the two expected files, verifying all bytes before writing."""
    manifest = json.loads((root / "artifacts/retrieval-index.json").read_text("utf-8"))
    archive = (root / "artifacts/retrieval-index.zip").read_bytes()
    corpus = root / "data/processed/articles.jsonl"
    search_records = root / "data/processed/search_records.jsonl"
    if sha256(archive) != manifest["archive_sha256"]:
        raise ValueError("Release archive checksum mismatch.")
    if sha256(corpus.read_bytes()) != manifest["corpus_sha256"]:
        raise ValueError("Frozen corpus checksum mismatch.")
    if sha256(search_records.read_bytes()) != manifest["search_records_sha256"]:
        raise ValueError("Search records checksum mismatch.")
    names = {"embeddings.npy", "index_records.jsonl"}
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        if set(bundle.namelist()) != names or len(bundle.namelist()) != 2:
            raise ValueError("Unexpected archive members.")
        payload = {name: bundle.read(name) for name in names}
    for name, data in payload.items():
        if sha256(data) != manifest["files"][name]:
            raise ValueError("Release member checksum mismatch.")
    output.mkdir(parents=True, exist_ok=True)
    for name, data in payload.items():
        target = output / name
        if target.exists() and sha256(target.read_bytes()) != manifest["files"][name]:
            raise ValueError(
                "Existing index differs from release; choose a new output directory."
            )
    for name, data in payload.items():
        target = output / name
        if not target.exists():
            temporary = output / (name + ".tmp")
            temporary.write_bytes(data)
            os.replace(temporary, target)
    result = validate_index(output, corpus)
    vectors = np.load(output / "embeddings.npy", allow_pickle=False)
    if vectors.shape != (manifest["record_count"], manifest["dimensions"]):
        raise ValueError("Release dimensions mismatch.")
    if read_records(output / "index_records.jsonl") != read_records(search_records):
        raise ValueError("Search record order/content mismatch.")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/index"))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = restore(args.output)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
