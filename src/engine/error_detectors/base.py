from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar

_DETECTOR_REGISTRY: dict[str, type[BaseDetector]] = {}


@dataclass
class DetectionResult:
    detector_id: str
    category: str
    severity: str
    summary: str
    details: dict = field(default_factory=dict)
    recommended_action: str = ""
    checked_at: str = ""

    def __post_init__(self):
        if not self.checked_at:
            self.checked_at = datetime.now().astimezone().isoformat(timespec="seconds")


class BaseDetector(ABC):
    id: ClassVar[str] = ""
    name: ClassVar[str] = ""
    category: ClassVar[str] = ""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    @abstractmethod
    def check(self) -> DetectionResult: ...


def register_detector(cls):
    if not issubclass(cls, BaseDetector):
        raise TypeError(f"{cls.__name__} must inherit BaseDetector")
    detector_id = getattr(cls, "id", None)
    if not detector_id:
        raise ValueError(f"{cls.__name__} must define class variable 'id'")
    _DETECTOR_REGISTRY[detector_id] = cls
    return cls


def get_registered_detectors() -> dict[str, type[BaseDetector]]:
    return dict(_DETECTOR_REGISTRY)
