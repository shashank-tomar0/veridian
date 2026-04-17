"""Model download script — pre-downloads all ML models from HuggingFace Hub.

Usage:
    python -m scripts.download_models [--models all|text|image|audio|video]
"""

from __future__ import annotations

import argparse
import sys

import structlog

logger = structlog.get_logger()

MODEL_REGISTRY: dict[str, list[dict[str, str]]] = {
    "text": [
        {"repo": "tiiuae/falcon-7b", "files": ["config.json"]},
        {"repo": "tiiuae/falcon-7b-instruct", "files": ["config.json"]},
        {"repo": "google/muril-base-cased", "files": ["config.json"]},
    ],
    "image": [
        {"repo": "openai/clip-vit-large-patch14", "files": ["config.json"]},
    ],
    "audio": [],
    "video": [],
}


def download_model(repo_id: str, filenames: list[str] | None = None) -> None:
    """Download a model from HuggingFace Hub."""
    try:
        from huggingface_hub import snapshot_download

        logger.info("download.start", repo=repo_id)
        snapshot_download(
            repo_id=repo_id,
            cache_dir=".cache/models",
            ignore_patterns=["*.bin", "*.safetensors"] if not filenames else None,
        )
        logger.info("download.complete", repo=repo_id)
    except Exception as exc:
        logger.error("download.failed", repo=repo_id, error=str(exc))


def main() -> None:
    parser = argparse.ArgumentParser(description="Download ML models")
    parser.add_argument(
        "--models",
        default="all",
        choices=["all", "text", "image", "audio", "video"],
        help="Which model groups to download",
    )
    args = parser.parse_args()

    groups = (
        MODEL_REGISTRY.keys()
        if args.models == "all"
        else [args.models]
    )

    for group in groups:
        for model in MODEL_REGISTRY.get(group, []):
            download_model(model["repo"], model.get("files"))

    logger.info("download.all_complete")


if __name__ == "__main__":
    main()
