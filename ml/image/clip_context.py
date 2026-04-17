import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from ml.base import DetectionResult

class CLIPContextDetector:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.model_id = "openai/clip-vit-large-patch14"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = None
        self.model = None
        self._is_loaded = False

    def load_model(self):
        if self._is_loaded:
            return
        
        self.model = CLIPModel.from_pretrained(self.model_id).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(self.model_id)
        self._is_loaded = True

    def predict(self, image_path: str, caption: str) -> DetectionResult:
        if not self._is_loaded:
            self.load_model()
            
        image = Image.open(image_path).convert('RGB')
        
        inputs = self.processor(text=[caption], images=image, return_tensors="pt", padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            
        # Cosine similarity is the main output (logits_per_image) generally scaled
        # Standard CLIP logit score matrix: (1 x 1). To get cosine similarity, we can extract image/text embeds directly
        image_embeds = outputs.image_embeds
        text_embeds = outputs.text_embeds
        
        # Normalize
        image_embeds = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)
        text_embeds = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)
        
        cosine_sim = torch.matmul(image_embeds, text_embeds.t()).item()
        
        mismatch_score = 1.0 - max(cosine_sim, 0.0) # mismatch increases if sim is low
        
        is_mismatch = cosine_sim < 0.25
        
        return DetectionResult(
            score=mismatch_score,
            metadata={"cosine_similarity": cosine_sim},
            verdict="OUT_OF_CONTEXT" if is_mismatch else "MATCHES_CONTEXT"
        )
