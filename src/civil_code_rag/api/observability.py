"""Request IDs, structured audit records and Prometheus-format metrics."""

import hashlib
import json
import logging
import re
import sys
import threading
import time
import uuid
from collections import defaultdict
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

from civil_code_rag.config import PROJECT_ROOT, Settings
from civil_code_rag.release_artifact import MODEL_NAME, MODEL_REVISION

REQUEST_ID_HEADER = "X-Request-ID"
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")
KNOWN_PATHS = {"/health", "/ask", "/metrics"}
AUDITED_PATHS = {"/ask", "/metrics"}
GENERATION_ROUTES = {"explain", "semantic"}
LATENCY_BUCKETS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0)

audit_logger = logging.getLogger("civil_code_rag.audit")
_audit_lock = threading.Lock()
_audit_configured = False


def resolve_request_id(incoming: str | None) -> str:
    """Reuse a caller's well-formed request ID, otherwise create one."""

    if incoming and REQUEST_ID_PATTERN.fullmatch(incoming):
        return incoming
    return uuid.uuid4().hex


def metric_path(path: str) -> str:
    """Keep label cardinality bounded by collapsing unknown paths."""

    return path if path in KNOWN_PATHS else "other"


def question_fingerprint(question: str) -> str:
    """Hash the question so repeats can be correlated without storing its text."""

    return hashlib.sha256(question.encode("utf-8")).hexdigest()


@lru_cache
def index_version() -> str:
    """Return the release-index archive checksum that answers were served from."""

    try:
        manifest = json.loads(
            (PROJECT_ROOT / "artifacts" / "retrieval-index.json").read_text("utf-8")
        )
        return manifest["archive_sha256"]
    except (OSError, ValueError, KeyError):
        return "unknown"


def configure_audit_logger(settings: Settings) -> None:
    """Attach stdout and optional file handlers once per process."""

    global _audit_configured
    with _audit_lock:
        if _audit_configured:
            return
        audit_logger.setLevel(logging.INFO)
        audit_logger.propagate = False
        audit_logger.addHandler(logging.StreamHandler(sys.stdout))
        if settings.audit_log_path is not None:
            Path(settings.audit_log_path).parent.mkdir(parents=True, exist_ok=True)
            audit_logger.addHandler(
                logging.FileHandler(settings.audit_log_path, encoding="utf-8")
            )
        _audit_configured = True


def build_audit_record(
    *,
    request_id: str,
    method: str,
    path: str,
    status_code: int,
    latency_seconds: float,
    audit: dict,
    settings: Settings,
) -> dict:
    """Assemble one audit record; the raw question text is never included."""

    route = audit.get("route")
    return {
        "event": "api_audit",
        "timestamp": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "latency_ms": round(latency_seconds * 1000, 2),
        "client_id": audit.get("client_id"),
        "outcome": audit.get("outcome") or default_outcome(status_code),
        "route": route,
        "language": audit.get("language"),
        "cited_article_ids": audit.get("cited_article_ids"),
        "question_sha256": audit.get("question_sha256"),
        "question_chars": audit.get("question_chars"),
        "llm_model": settings.llm_model if route in GENERATION_ROUTES else None,
        "embedding_model": MODEL_NAME,
        "embedding_model_revision": MODEL_REVISION,
        "index_archive_sha256": index_version(),
    }


def default_outcome(status_code: int) -> str:
    if status_code < 400:
        return "ok"
    if status_code == 422:
        return "invalid_request"
    return "error"


def write_audit(record: dict, settings: Settings) -> None:
    configure_audit_logger(settings)
    audit_logger.info(json.dumps(record, ensure_ascii=False))


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _labels(**labels: str) -> str:
    return ",".join(f'{key}="{_escape(str(value))}"' for key, value in labels.items())


class Metrics:
    """In-process counters and latency histograms rendered in Prometheus text."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.started_at = time.time()
        self.requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self.latency_buckets: dict[str, list[int]] = defaultdict(
            lambda: [0] * len(LATENCY_BUCKETS)
        )
        self.latency_sum: dict[str, float] = defaultdict(float)
        self.latency_count: dict[str, int] = defaultdict(int)
        self.ask_outcomes: dict[tuple[str, str], int] = defaultdict(int)

    def observe_request(
        self, method: str, path: str, status_code: int, latency_seconds: float
    ) -> None:
        with self._lock:
            self.requests[(method, path, status_code)] += 1
            buckets = self.latency_buckets[path]
            for position, upper in enumerate(LATENCY_BUCKETS):
                if latency_seconds <= upper:
                    buckets[position] += 1
            self.latency_sum[path] += latency_seconds
            self.latency_count[path] += 1

    def observe_ask(self, outcome: str, route: str | None) -> None:
        with self._lock:
            self.ask_outcomes[(outcome, route or "none")] += 1

    def render(self) -> str:
        with self._lock:
            lines = [
                "# HELP civil_code_rag_process_start_time_seconds Process start time.",
                "# TYPE civil_code_rag_process_start_time_seconds gauge",
                f"civil_code_rag_process_start_time_seconds {self.started_at:.3f}",
                "# HELP civil_code_rag_http_requests_total HTTP requests handled.",
                "# TYPE civil_code_rag_http_requests_total counter",
            ]
            for (method, path, status), count in sorted(self.requests.items()):
                labels = _labels(method=method, path=path, status=str(status))
                lines.append(f"civil_code_rag_http_requests_total{{{labels}}} {count}")
            name = "civil_code_rag_http_request_duration_seconds"
            lines += [
                f"# HELP {name} HTTP request latency.",
                f"# TYPE {name} histogram",
            ]
            for path in sorted(self.latency_count):
                for upper, count in zip(LATENCY_BUCKETS, self.latency_buckets[path]):
                    labels = _labels(path=path, le=str(upper))
                    lines.append(f"{name}_bucket{{{labels}}} {count}")
                total = self.latency_count[path]
                lines.append(f'{name}_bucket{{{_labels(path=path, le="+Inf")}}} {total}')
                lines.append(
                    f"{name}_sum{{{_labels(path=path)}}} {self.latency_sum[path]:.6f}"
                )
                lines.append(f"{name}_count{{{_labels(path=path)}}} {total}")
            lines += [
                "# HELP civil_code_rag_ask_total /ask results by outcome and route.",
                "# TYPE civil_code_rag_ask_total counter",
            ]
            for (outcome, route), count in sorted(self.ask_outcomes.items()):
                labels = _labels(outcome=outcome, route=route)
                lines.append(f"civil_code_rag_ask_total{{{labels}}} {count}")
        return "\n".join(lines) + "\n"


METRICS = Metrics()
