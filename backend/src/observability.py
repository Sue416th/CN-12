import contextvars
import logging
import re
import time
import uuid
from typing import Any

from fastapi import Request


TRACE_ID_HEADER = "x-trace-id"
_trace_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")

logger = logging.getLogger("trailmark")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [trace=%(trace_id)s] %(message)s",
    )


class TraceIdAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs.setdefault("extra", {})
        kwargs["extra"]["trace_id"] = get_trace_id()
        return msg, kwargs


log = TraceIdAdapter(logger, {})


def get_trace_id() -> str:
    return _trace_id_ctx.get()


def set_trace_id(trace_id: str):
    return _trace_id_ctx.set(trace_id)


def reset_trace_id(token):
    _trace_id_ctx.reset(token)


def generate_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def redact_sensitive_text(text: str) -> str:
    if not text:
        return text
    masked = re.sub(r"(bearer\s+)[a-zA-Z0-9\-\._~\+\/]+=*", r"\1***", text, flags=re.IGNORECASE)
    masked = re.sub(r"(password|token|secret|api[_-]?key)\s*[:=]\s*['\"]?[^'\"\s,}]+", r"\1=***", masked, flags=re.IGNORECASE)
    return masked


def redact_obj(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            key_text = str(key).lower()
            if any(token in key_text for token in ("password", "token", "secret", "api_key", "authorization")):
                redacted[key] = "***"
            else:
                redacted[key] = redact_obj(item)
        return redacted
    if isinstance(value, list):
        return [redact_obj(item) for item in value]
    if isinstance(value, str):
        return redact_sensitive_text(value)
    return value


async def trace_middleware(request: Request, call_next):
    incoming = request.headers.get(TRACE_ID_HEADER, "").strip()
    trace_id = incoming if incoming else generate_trace_id()
    token = set_trace_id(trace_id)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        log.info("%s %s -> %s (%.1fms)", request.method, request.url.path, response.status_code, elapsed_ms)
        response.headers["X-Trace-Id"] = trace_id
        return response
    finally:
        reset_trace_id(token)
