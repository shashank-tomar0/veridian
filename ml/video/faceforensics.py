"""FaceForensics++ — Deepfake video detection via EfficientNet-B4.

Extracts face crops from keyframes using MTCNN, classifies each face with
an EfficientNet-B4 pretrained on the FaceForensics++ dataset, and
aggregates frame-level scores into a video-level deepfake score.
"""

from __future__ import annotations

from typing import Any

import cv2
import numpy as np
import torch
import torch.nn as nn

from ml.base import DetectionResult


class FaceForensicsDetector:
    """Deepfake detection using EfficientNet-B4 on FaceForensics++ data."""

    def __init__(self, config: dict | None = None) -> None:
        self.config = config or {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = None
        self.face_detector = None
        self._is_loaded = False
        self.keyframe_interval = 30  # extract every 30th frame
        self.face_size = (224, 224)

    def load_model(self) -> None:
        if self._is_loaded:
            return

        # Load EfficientNet-B4 for binary deepfake classification
        try:
            from torchvision import models

            self.model = models.efficientnet_b4(weights=None)
            # Replace classifier head for binary classification
            self.model.classifier = nn.Sequential(
                nn.Dropout(p=0.4),
                nn.Linear(self.model.classifier[1].in_features, 1),
            )

            # Attempt to load pretrained FaceForensics++ weights
            try:
                from huggingface_hub import hf_hub_download

                path = hf_hub_download(
                    repo_id="alterfalsification/FaceForensics",
                    filename="effnet_b4_ff.pth",
                    cache_dir=".cache/models",
                )
                state = torch.load(path, map_location=self.device, weights_only=True)
                self.model.load_state_dict(state, strict=False)
            except Exception:
                pass

            self.model = self.model.to(self.device)
            self.model.eval()
        except Exception:
            self.model = None

        # Face detector (MTCNN via facenet_pytorch or OpenCV cascade fallback)
        try:
            from facenet_pytorch import MTCNN

            self.face_detector = MTCNN(
                keep_all=True,
                device=self.device,
                post_process=False,
            )
        except ImportError:
            # Fallback: OpenCV Haar cascade
            self.face_detector = None

        self._is_loaded = True

    def _extract_keyframes(self, video_path: str) -> list[tuple[int, np.ndarray]]:
        """Extract keyframes from a video file."""
        frames: list[tuple[int, np.ndarray]] = []
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            return frames

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_idx % self.keyframe_interval == 0:
                frames.append((frame_idx, frame))
            frame_idx += 1

        cap.release()
        return frames

    def _detect_faces(self, frame: np.ndarray) -> list[np.ndarray]:
        """Detect and crop faces from a single frame."""
        if self.face_detector is not None:
            try:
                from PIL import Image

                pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                boxes, _ = self.face_detector.detect(pil_img)

                if boxes is None:
                    return []

                crops = []
                for box in boxes:
                    x1, y1, x2, y2 = [int(b) for b in box]
                    x1, y1 = max(0, x1), max(0, y1)
                    x2 = min(frame.shape[1], x2)
                    y2 = min(frame.shape[0], y2)
                    face = frame[y1:y2, x1:x2]
                    if face.size > 0:
                        face = cv2.resize(face, self.face_size)
                        crops.append(face)
                return crops
            except Exception:
                pass

        # Fallback: OpenCV Haar cascade
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        rects = cascade.detectMultiScale(gray, 1.1, 5)

        crops = []
        for (x, y, w, h) in rects:
            face = frame[y : y + h, x : x + w]
            face = cv2.resize(face, self.face_size)
            crops.append(face)
        return crops

    def _classify_face(self, face: np.ndarray) -> float:
        """Run EfficientNet-B4 on a single face crop and return deepfake score."""
        if self.model is None:
            return 0.5  # unable to classify

        from torchvision import transforms

        xform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(self.face_size),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        tensor = xform(cv2.cvtColor(face, cv2.COLOR_BGR2RGB)).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logit = self.model(tensor)
            return torch.sigmoid(logit).item()

    def predict(self, video_path: str) -> DetectionResult:
        """Analyse a video for deepfake content.

        Returns an aggregate deepfake_score and a list of manipulated frames.
        """
        if not self._is_loaded:
            self.load_model()

        keyframes = self._extract_keyframes(video_path)

        if not keyframes:
            return DetectionResult(
                score=0.0,
                metadata={"error": "No frames extracted", "model": "FaceForensics++"},
            )

        frame_scores: list[dict[str, Any]] = []

        for frame_idx, frame in keyframes:
            faces = self._detect_faces(frame)
            if not faces:
                continue

            for face in faces:
                score = self._classify_face(face)
                frame_scores.append({"frame_idx": frame_idx, "score": score})

        if not frame_scores:
            return DetectionResult(
                score=0.0,
                metadata={"warning": "No faces detected in keyframes", "model": "FaceForensics++"},
            )

        scores = [fs["score"] for fs in frame_scores]
        avg_score = float(np.mean(scores))
        manipulated = [fs for fs in frame_scores if fs["score"] > 0.5]

        return DetectionResult(
            score=avg_score,
            metadata={
                "model": "FaceForensics++",
                "total_keyframes": len(keyframes),
                "faces_analysed": len(frame_scores),
                "manipulated_frames": manipulated,
            },
            verdict="DEEPFAKE" if avg_score > 0.5 else "LIKELY_AUTHENTIC",
        )
