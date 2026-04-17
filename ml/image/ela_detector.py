import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import io
import base64
from ml.base import DetectionResult

class ELADetector:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.quality = 90
        # ELA doesn't require loaded weights, but follows interface
        self._is_loaded = True 

    def load_model(self):
        pass

    def predict(self, image_path: str) -> DetectionResult:
        original = Image.open(image_path).convert('RGB')
        
        # Save at a resaved quality to compute difference
        buffer = io.BytesIO()
        original.save(buffer, 'JPEG', quality=self.quality)
        buffer.seek(0)
        resaved = Image.open(buffer)
        
        # Calculate pixel-wise absolute difference
        diff = ImageChops.difference(original, resaved)
        
        # Enhance difference to detect forged zones
        extrema = diff.getextrema()
        max_diff = max([ex[1] for ex in extrema])
        scale = 255.0 / max_diff if max_diff != 0 else 1.0
        ela_img = ImageEnhance.Brightness(diff).enhance(scale)
        
        # Compute scalar anomaly score (variance of difference map)
        arr = np.array(ela_img)
        score = float(np.mean(arr) / 255.0)  # simple normalized metric
        
        # Convert heatmap to base64 for API returning
        out_buffer = io.BytesIO()
        ela_img.save(out_buffer, format="PNG")
        heatmap_b64 = base64.b64encode(out_buffer.getvalue()).decode("utf-8")
        
        return DetectionResult(
            score=min(score * 10, 1.0), # amplify heuristic
            metadata={"ela_heatmap_base64": heatmap_b64}
        )
