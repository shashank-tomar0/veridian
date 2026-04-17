import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from ml.base import DetectionResult

class MurilClassifier:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.model_id = "google/muril-base-cased"
        self.device = "cpu" # Forced to CPU for stability on Python 3.13
        self.tokenizer = None
        self.model = None
        self._is_loaded = False

    def load_model(self):
        if self._is_loaded:
            return
        
        print(f"Loading MuRIL model ({self.model_id}) on {self.device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_id,
            num_labels=2
        ).to(self.device)
        
        # Only use half precision if on CUDA (CPU doesn't support many half-precision ops)
        if self.device == "cuda":
            self.model = self.model.half()
            
        self.model.eval()
        self._is_loaded = True
        print(f"MuRIL model loaded successfully on {self.device}.")

    def predict(self, text: str) -> DetectionResult:
        self.load_model()
            
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512).to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            manipulated_score = probabilities[0][1].item()
            
        return DetectionResult(
            score=manipulated_score,
            metadata={"language": "auto", "device": self.device},
            verdict="MANIPULATED" if manipulated_score > 0.6 else "AUTHENTIC"
        )
