import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from ml.base import DetectionResult

class BinocularsDetector:
    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # CPU-Friendly models vs Production-grade Falcon models
        if self.device == "cuda":
            self.observer_model_id = "tiiuae/falcon-7b"
            self.performer_model_id = "tiiuae/falcon-7b-instruct"
        else:
            # Using smaller models on CPU to avoid 14GB+ RAM requirement
            self.observer_model_id = "gpt2"
            self.performer_model_id = "gpt2-medium"
            print(f"Hardware Constraint: Switching to CPU-friendly models ({self.observer_model_id}/{self.performer_model_id})")

        self.tokenizer = None
        self.observer_model = None
        self.performer_model = None
        self._is_loaded = False

    def load_model(self):
        if self._is_loaded:
            return
        
        # We load them in 8-bit or 4-bit to save memory generally, but here we assume raw or standard float16 handling
        self.tokenizer = AutoTokenizer.from_pretrained(self.observer_model_id)
        
        # Load observer
        dtype = torch.float16 if self.device == "cuda" else torch.float32
        
        # On CPU, device_map can sometimes cause issues even with 'accelerate' installed
        # We explicitly handle CPU vs CUDA loading
        self.observer_model = AutoModelForCausalLM.from_pretrained(
            self.observer_model_id, 
            torch_dtype=dtype, 
            device_map=self.device if self.device != "cpu" else None,
            low_cpu_mem_usage=True
        )
        if self.device == "cpu":
            self.observer_model = self.observer_model.to("cpu")
        self.observer_model.eval()

        # Load performer
        self.performer_model = AutoModelForCausalLM.from_pretrained(
            self.performer_model_id, 
            torch_dtype=dtype, 
            device_map=self.device if self.device != "cpu" else None,
            low_cpu_mem_usage=True
        )
        if self.device == "cpu":
            self.performer_model = self.performer_model.to("cpu")
        self.performer_model.eval()
        self._is_loaded = True

    def _compute_perplexity(self, model, inputs):
        with torch.no_grad():
            outputs = model(**inputs, labels=inputs["input_ids"])
            return torch.exp(outputs.loss).item()

    def predict(self, text: str) -> DetectionResult:
        if not self._is_loaded:
            self.load_model()
            
        inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
        
        # Calculate perplexity from observer model (P_observer)
        ppl_observer = self._compute_perplexity(self.observer_model, inputs)
        
        # Calculate perplexity from performer model (P_performer)
        ppl_performer = self._compute_perplexity(self.performer_model, inputs)
        
        # Binoculars metric: log(P_observer) / log(P_performer)
        # However, for score translation we generally normalize it
        import math
        try:
            score = math.log(ppl_observer) / math.log(ppl_performer)
        except Exception:
            score = 1.0
            
        # Threshold mapping (simplification for platform bounds):
        # AI generated typically results in lower relative score depending on normalization
        normalized_score = min(max(abs(1.0 - score), 0.0), 1.0) # heuristic mapping for 0-1
        
        return DetectionResult(
            score=normalized_score,
            metadata={
                "observer_ppl": ppl_observer,
                "performer_ppl": ppl_performer,
                "raw_binoculars_score": score
            }
        )
