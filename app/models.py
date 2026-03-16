from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class FileStatus(Enum):
    PENDING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    ERROR = auto()


@dataclass
class MonitoredFile:
    """감시 대상 파일의 상태를 표현하는 도메인 모델."""

    path: str
    name: str
    watch_root: str
    size: int = 0
    last_changed_at: float = 0.0
    status: FileStatus = FileStatus.PENDING
    started_notified: bool = False
    completed_notified: bool = False
    row_index: Optional[int] = field(default=None)

