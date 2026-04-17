# ML Models Reference

## Overview

All ML models are lazy-loaded on first use via `huggingface_hub.hf_hub_download()`. Model weights are **never committed** to the repository. Models download to `.cache/models/` on first invocation.

## Model Inventory

### Text Detectors

#### Binoculars (Zero-shot AI Text Detection)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/text/binoculars.py`                         |
| **Models**      | `tiiuae/falcon-7b` (observer), `tiiuae/falcon-7b-instruct` (performer) |
| **License**     | Apache 2.0                                      |
| **Input**       | Raw text string                                 |
| **Output**      | Score 0–1 (higher = more likely AI-generated)   |
| **Method**      | Perplexity ratio between observer and performer models |
| **VRAM**        | ~14 GB (both models in float16)                 |
| **Latency**     | ~2–5s per text sample                           |

#### MuRIL (Semantic Manipulation Classifier)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/text/muril_classifier.py`                   |
| **Model**       | `google/muril-base-cased`                       |
| **License**     | Apache 2.0                                      |
| **Input**       | Text (max 512 tokens), supports 17 Indian languages + English |
| **Output**      | Score 0–1, verdict: AUTHENTIC / MANIPULATED     |
| **Method**      | Fine-tuned classification head on MuRIL encoder |
| **VRAM**        | ~1 GB                                           |
| **Latency**     | ~100–300ms                                      |

### Image Detectors

#### ELA (Error Level Analysis)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/image/ela_detector.py`                      |
| **Model**       | None (signal processing)                        |
| **License**     | N/A                                             |
| **Input**       | Image file path (JPEG)                          |
| **Output**      | Forgery score 0–1 + ELA heatmap (base64 PNG)    |
| **Method**      | JPEG recompression → pixel-wise difference map   |
| **VRAM**        | 0 (CPU only)                                    |
| **Latency**     | ~50–200ms                                       |

#### DIRE (Diffusion Reconstruction Error)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/image/dire_detector.py`                     |
| **Model**       | `lsml/DIRE` (ResNet-50 backbone)                |
| **License**     | Research-only                                   |
| **Input**       | Image file path                                 |
| **Output**      | AI-generated score 0–1                          |
| **Method**      | Diffusion model reconstructs image; high MSE = AI |
| **VRAM**        | ~2 GB                                           |
| **Latency**     | ~1–3s                                           |

#### CLIP (Out-of-Context Detection)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/image/clip_context.py`                      |
| **Model**       | `openai/clip-vit-large-patch14`                 |
| **License**     | MIT                                             |
| **Input**       | Image file path + caption text                  |
| **Output**      | Mismatch score 0–1 (cosine similarity < 0.25 = mismatch) |
| **VRAM**        | ~2 GB                                           |
| **Latency**     | ~200–500ms                                      |

### Audio Detectors

#### RawNet2 (Voice Spoof Detection)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/audio/rawnet2.py`                           |
| **Model**       | Custom SincConv + ResBlock + GRU architecture   |
| **Weights**     | ASVspoof 2019 LA                                |
| **License**     | Research-only                                   |
| **Input**       | 16kHz mono WAV (file path or bytes)             |
| **Output**      | Spoof score 0–1                                 |
| **Method**      | Raw waveform → sinc filters → GRU → binary     |
| **VRAM**        | ~500 MB                                         |
| **Latency**     | ~200–500ms per 4s clip                          |

#### Resemblyzer (Speaker Verification)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/audio/resemblyzer.py`                       |
| **Model**       | Resemblyzer VoiceEncoder                        |
| **License**     | Apache 2.0                                      |
| **Input**       | 16kHz mono WAV                                  |
| **Output**      | 256-dim d-vector, speaker_match: bool, confidence 0–1 |
| **Method**      | Generate embedding → cosine similarity vs voiceprint DB |
| **VRAM**        | ~200 MB                                         |
| **Latency**     | ~100–300ms                                      |

### Video Detectors

#### FaceForensics++ (Deepfake Detection)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/video/faceforensics.py`                     |
| **Model**       | EfficientNet-B4                                 |
| **Dataset**     | FaceForensics++ (all manipulation methods)      |
| **License**     | Research-only (FaceForensics++ terms)           |
| **Input**       | Video file path                                 |
| **Output**      | Deepfake score 0–1 + manipulated frames list    |
| **Method**      | MTCNN face crops → per-frame EfficientNet → aggregate |
| **VRAM**        | ~4 GB                                           |
| **Latency**     | ~5–30s depending on video length                |

#### Temporal Consistency Analysis

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/video/temporal.py`                          |
| **Model**       | None (signal processing)                        |
| **License**     | N/A                                             |
| **Input**       | Video file path                                 |
| **Output**      | Temporal anomaly score 0–1 + anomaly frame indices |
| **Method**      | Optical flow (LK) + Laplacian noise → z-score outliers |
| **VRAM**        | 0 (CPU only)                                    |
| **Latency**     | ~2–10s                                          |

#### SyncNet (Lip-Sync Verification)

| Property        | Value                                           |
| --------------- | ----------------------------------------------- |
| **Module**      | `ml/video/syncsnet.py`                          |
| **Model**       | Custom dual-encoder (audio CNN + visual CNN)    |
| **License**     | Research-only                                   |
| **Input**       | Video file path                                 |
| **Output**      | Sync score 0–1 (low = dubbed/manipulated)       |
| **Method**      | Lip crops + mel spectrograms → cosine similarity |
| **VRAM**        | ~1 GB                                           |
| **Latency**     | ~3–10s                                          |
