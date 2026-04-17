"""Temporal consistency analysis for video manipulation detection.

Extracts optical flow between consecutive frames and analyses noise profiles
to detect anomalous temporal discontinuities indicative of editing.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np

from ml.base import DetectionResult


class TemporalConsistencyDetector:
    """Detect temporal manipulation artefacts via optical flow analysis."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self._is_loaded = True  # No model weights required
        self.flow_threshold = 2.0  # std deviations for anomaly
        self.frame_skip = 1  # analyse every N frames
        self.max_frames = 300  # cap for performance

    def load_model(self) -> None:
        """No model to load — this is a signal-processing detector."""
        pass

    def _extract_frames(self, video_path: str) -> list[np.ndarray]:
        """Extract grayscale frames from a video."""
        cap = cv2.VideoCapture(video_path)
        frames: list[np.ndarray] = []

        if not cap.isOpened():
            return frames

        count = 0
        while len(frames) < self.max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if count % (self.frame_skip + 1) == 0:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                frames.append(gray)
            count += 1

        cap.release()
        return frames

    def _compute_optical_flow_magnitudes(self, frames: list[np.ndarray]) -> list[float]:
        """Compute mean optical flow magnitude between consecutive frame pairs."""
        magnitudes: list[float] = []

        for i in range(len(frames) - 1):
            prev = frames[i]
            curr = frames[i + 1]

            # Lucas-Kanade sparse optical flow
            pts = cv2.goodFeaturesToTrack(prev, maxCorners=200, qualityLevel=0.01, minDistance=10)

            if pts is None or len(pts) == 0:
                magnitudes.append(0.0)
                continue

            new_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev, curr, pts, None)

            if new_pts is None:
                magnitudes.append(0.0)
                continue

            # Keep only good matches
            good_mask = status.flatten() == 1
            if not good_mask.any():
                magnitudes.append(0.0)
                continue

            old = pts[good_mask]
            new = new_pts[good_mask]

            displacements = np.sqrt(np.sum((new - old) ** 2, axis=-1))
            magnitudes.append(float(np.mean(displacements)))

        return magnitudes

    def _compute_noise_profile(self, frames: list[np.ndarray]) -> list[float]:
        """Compute per-frame noise energy using Laplacian variance."""
        noise_vals: list[float] = []
        for frame in frames:
            laplacian = cv2.Laplacian(frame, cv2.CV_64F)
            noise_vals.append(float(laplacian.var()))
        return noise_vals

    def _detect_anomalies(self, signal: list[float]) -> list[int]:
        """Return indices where signal deviates by > threshold std devs."""
        if len(signal) < 3:
            return []

        arr = np.array(signal)
        mean = np.mean(arr)
        std = np.std(arr)

        if std < 1e-6:
            return []

        z_scores = np.abs((arr - mean) / std)
        return [int(i) for i in np.where(z_scores > self.flow_threshold)[0]]

    def predict(self, video_path: str) -> DetectionResult:
        """Analyse temporal consistency of a video.

        Returns a temporal_anomaly_score and details about detected discontinuities.
        """
        frames = self._extract_frames(video_path)

        if len(frames) < 3:
            return DetectionResult(
                score=0.0,
                metadata={"error": "Insufficient frames for temporal analysis"},
            )

        # Optical flow analysis
        flow_mags = self._compute_optical_flow_magnitudes(frames)
        flow_anomalies = self._detect_anomalies(flow_mags)

        # Noise profile analysis
        noise_profile = self._compute_noise_profile(frames)
        noise_anomalies = self._detect_anomalies(noise_profile)

        # Combine anomaly indices
        all_anomalies = sorted(set(flow_anomalies) | set(noise_anomalies))

        # Score: proportion of anomalous transitions
        total_transitions = max(len(flow_mags), 1)
        anomaly_ratio = len(all_anomalies) / total_transitions
        # Clamp and scale
        score = min(anomaly_ratio * 5.0, 1.0)  # amplify

        return DetectionResult(
            score=score,
            metadata={
                "model": "TemporalConsistency",
                "total_frames_analysed": len(frames),
                "flow_anomaly_frames": flow_anomalies,
                "noise_anomaly_frames": noise_anomalies,
                "total_anomalies": len(all_anomalies),
                "avg_flow_magnitude": float(np.mean(flow_mags)) if flow_mags else 0.0,
            },
            verdict="TEMPORAL_ANOMALY" if score > 0.3 else "TEMPORALLY_CONSISTENT",
        )
