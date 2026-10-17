"""Bounded session diagnostics: metadata only, never request/response bodies or URLs."""

import copy
import re
import threading
import time
import uuid
from collections import deque
from contextvars import ContextVar
from datetime import datetime, timezone

LIMIT = 200
_entries = deque(maxlen=LIMIT)
_lock = threading.RLock()
_active = ContextVar("ai_diagnostic_trace", default=None)
_operation = ContextVar("ai_diagnostic_operation", default="ai")
REASONS = {"stop", "length", "tool_calls", "function_call", "content_filter", "end_turn", "max_tokens",
           "stop_sequence", "pause_turn", "refusal", "completed", "incomplete", "cancelled", "failed"}
ISSUES = {"http_error", "connection_error", "timeout", "invalid_json", "invalid_response", "response_too_large",
          "stream_interrupted", "stream_error", "length", "tool_call", "refused", "missing_finish", "incomplete",
          "empty_output", "schema_error", "configuration_error", "provider_error", "unexpected_error"}


def begin_operation(path):
    return _operation.set({"/api/generate": "generate", "/api/review": "review",
                           "/api/conversion/compile": "conversion"}.get(path, "ai"))


def end_operation(token):
    _operation.reset(token)


def sanitized_model(value, secrets):
    for secret in secrets:
        if isinstance(secret, str) and secret:
            value = value.replace(secret, "[redacted]")
    value = re.sub(r"(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]+|github_pat_[A-Za-z0-9_]+)", "[redacted]", value)
    return value[:200]


class Trace:
    def __init__(self, provider):
        self.row = {"id": uuid.uuid4().hex[:16], "started_at": datetime.now(timezone.utc).isoformat(),
                    "provider": provider if provider in ("openai", "claude", "ollama", "lmstudio") else "unknown",
                    "operation": _operation.get(), "status": "running", "outcome": "waiting", "model": "",
                    "_started": time.monotonic()}
        with _lock:
            _entries.append(self.row)
        self.token = _active.set(self)

    def configure(self, model, secrets, output_limit=16000):
        with _lock:
            self.row.update(model=sanitized_model(model, secrets), output_limit=output_limit)

    def finish(self, outcome):
        with _lock:
            self.row.update(status="success" if outcome == "ok" else "error",
                            outcome=self.row.get("_issue", outcome),
                            elapsed_ms=round((time.monotonic() - self.row["_started"]) * 1000))
        _active.reset(self.token)


def mark(issue):
    trace = _active.get()
    if trace and issue in ISSUES:
        with _lock:
            trace.row["_issue"] = issue


def transport(local, timeout, stream, http_status=None):
    trace = _active.get()
    if trace:
        with _lock:
            trace.row.update(local=bool(local), timeout_seconds=timeout, streaming=bool(stream))
            if type(http_status) is int and 100 <= http_status <= 599:
                trace.row["http_status"] = http_status


def response_metadata(value):
    trace = _active.get()
    if not trace or not isinstance(value, dict):
        return
    choices = value.get("choices")
    reason = value.get("stop_reason", value.get("done_reason", value.get("status")))
    if isinstance(choices, list) and choices and isinstance(choices[0], dict):
        reason = choices[0].get("finish_reason")
    safe = reason if isinstance(reason, str) and reason in REASONS else "missing" if reason is None else "other"
    usage = value.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    numbers = {"input_tokens": usage.get("prompt_tokens", usage.get("input_tokens", value.get("prompt_eval_count"))),
               "output_tokens": usage.get("completion_tokens", usage.get("output_tokens", value.get("eval_count"))),
               "total_tokens": usage.get("total_tokens")}
    details = usage.get("completion_tokens_details", usage.get("output_tokens_details", {}))
    if isinstance(details, dict):
        numbers["reasoning_tokens"] = details.get("reasoning_tokens")
    with _lock:
        trace.row["finish_reason"] = safe
        for key, number in numbers.items():
            if type(number) is int and 0 <= number <= 1_000_000_000:
                trace.row[key] = number
        detail = value.get("incomplete_details")
        if isinstance(detail, dict) and detail.get("reason") == "max_output_tokens":
            trace.row["_issue"] = "length"


def failure_from_response():
    trace = _active.get()
    reason = trace.row.get("finish_reason") if trace else None
    mark({"length": "length", "max_tokens": "length", "tool_calls": "tool_call", "function_call": "tool_call",
          "content_filter": "refused", "refusal": "refused", "missing": "missing_finish"}.get(reason, "incomplete"))


def listing():
    with _lock:
        rows = []
        for entry in reversed(_entries):
            row = {key: copy.deepcopy(value) for key, value in entry.items() if not key.startswith("_")}
            if entry["status"] == "running":
                row["elapsed_ms"] = round((time.monotonic() - entry["_started"]) * 1000)
            rows.append(row)
    return {"entries": rows, "limit": LIMIT, "session_only": True}


def clear_completed():
    with _lock:
        running = [entry for entry in _entries if entry["status"] == "running"]
        _entries.clear()
        _entries.extend(running)
