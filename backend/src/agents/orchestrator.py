import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, List, Optional

from src.observability import get_trace_id, log, redact_obj


class TaskState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    RETRYING = "retrying"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    TIMED_OUT = "timed_out"


@dataclass
class TaskTransition:
    from_state: TaskState
    to_state: TaskState
    attempt: int
    reason: str


@dataclass
class TaskResult:
    name: str
    state: TaskState
    attempts: int
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    trace_id: str = ""
    transitions: List[TaskTransition] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.state == TaskState.SUCCEEDED


class AgentOrchestrator:
    def __init__(self, default_timeout_seconds: float = 20.0, default_retries: int = 1):
        self.default_timeout_seconds = default_timeout_seconds
        self.default_retries = default_retries

    async def run_task(
        self,
        name: str,
        task_factory: Callable[[], Awaitable[Dict[str, Any]]],
        timeout_seconds: Optional[float] = None,
        retries: Optional[int] = None,
    ) -> TaskResult:
        timeout = timeout_seconds if timeout_seconds is not None else self.default_timeout_seconds
        max_retries = retries if retries is not None else self.default_retries

        trace_id = get_trace_id()
        attempts = 0
        transitions: List[TaskTransition] = []
        state = TaskState.CREATED

        while attempts <= max_retries:
            attempts += 1
            next_state = TaskState.RUNNING if attempts == 1 else TaskState.RETRYING
            transitions.append(TaskTransition(state, next_state, attempts, "attempt start"))
            state = next_state
            try:
                result = await asyncio.wait_for(task_factory(), timeout=timeout)
                transitions.append(TaskTransition(state, TaskState.SUCCEEDED, attempts, "completed"))
                log.info("task=%s attempt=%s state=succeeded payload=%s", name, attempts, redact_obj(result))
                return TaskResult(
                    name=name,
                    state=TaskState.SUCCEEDED,
                    attempts=attempts,
                    result=result,
                    trace_id=trace_id,
                    transitions=transitions,
                )
            except asyncio.TimeoutError:
                error = f"timeout after {timeout:.1f}s"
                transitions.append(TaskTransition(state, TaskState.TIMED_OUT, attempts, error))
                state = TaskState.TIMED_OUT
                log.warning("task=%s attempt=%s state=timed_out reason=%s", name, attempts, error)
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
                transitions.append(TaskTransition(state, TaskState.FAILED, attempts, error))
                state = TaskState.FAILED
                log.warning("task=%s attempt=%s state=failed reason=%s", name, attempts, error)

            if attempts > max_retries:
                break

        final_error = transitions[-1].reason if transitions else "unknown failure"
        return TaskResult(
            name=name,
            state=state,
            attempts=attempts,
            error=final_error,
            trace_id=trace_id,
            transitions=transitions,
        )
