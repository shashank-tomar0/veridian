from dataclasses import dataclass

@dataclass
class DetectionResult:
    score: float
    metadata: dict
    verdict: str | None = None
