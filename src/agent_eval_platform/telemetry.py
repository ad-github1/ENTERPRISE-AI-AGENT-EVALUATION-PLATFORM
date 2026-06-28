from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator


@dataclass(frozen=True, slots=True)
class SpanEvent:
    name: str
    attributes: dict[str, object]
    timestamp_ns: int


@dataclass(frozen=True, slots=True)
class SpanRecord:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time_ns: int
    end_time_ns: int
    attributes: dict[str, object]
    events: tuple[SpanEvent, ...] = ()


@dataclass(slots=True)
class ActiveSpan:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    start_time_ns: int
    attributes: dict[str, object]
    events: list[SpanEvent] = field(default_factory=list)

    def add_event(self, name: str, **attributes: object) -> None:
        self.events.append(SpanEvent(name=name, attributes=attributes, timestamp_ns=time.time_ns()))


class TelemetryRecorder:
    """Small OpenTelemetry-compatible trace recorder.

    The project stays dependency-free, but the exported JSON fields mirror the
    OTLP trace concepts: trace id, span id, parent span id, timestamps, and
    attributes.
    """

    def __init__(self) -> None:
        self.spans: list[SpanRecord] = []

    @contextmanager
    def span(
        self,
        name: str,
        *,
        trace_id: str | None = None,
        parent_span_id: str | None = None,
        **attributes: object,
    ) -> Iterator[ActiveSpan]:
        active = ActiveSpan(
            trace_id=trace_id or uuid.uuid4().hex,
            span_id=uuid.uuid4().hex[:16],
            parent_span_id=parent_span_id,
            name=name,
            start_time_ns=time.time_ns(),
            attributes=dict(attributes),
        )
        try:
            yield active
        finally:
            self.spans.append(
                SpanRecord(
                    trace_id=active.trace_id,
                    span_id=active.span_id,
                    parent_span_id=active.parent_span_id,
                    name=active.name,
                    start_time_ns=active.start_time_ns,
                    end_time_ns=time.time_ns(),
                    attributes=active.attributes,
                    events=tuple(active.events),
                )
            )

    def export_jsonl(self, path: str | Path) -> None:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for span in self.spans:
                handle.write(json.dumps(span_to_dict(span), sort_keys=True) + "\n")


def span_to_dict(span: SpanRecord) -> dict[str, object]:
    return {
        "trace_id": span.trace_id,
        "span_id": span.span_id,
        "parent_span_id": span.parent_span_id,
        "name": span.name,
        "start_time_unix_nano": span.start_time_ns,
        "end_time_unix_nano": span.end_time_ns,
        "attributes": span.attributes,
        "events": [
            {
                "name": event.name,
                "timestamp_unix_nano": event.timestamp_ns,
                "attributes": event.attributes,
            }
            for event in span.events
        ],
    }
