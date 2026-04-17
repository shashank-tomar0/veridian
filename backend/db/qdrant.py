from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models as qmodels
from backend.config import settings

class QdrantService:
    def __init__(self):
        self.client = AsyncQdrantClient(url=settings.qdrant_url)
        self.fact_corpus_name = "fact_corpus"
        self.claim_archive_name = "claim_archive"
        self.image_hashes_name = "image_hashes"

    async def initialize_collections(self):
        # Fact Corpus
        if not await self.client.collection_exists(self.fact_corpus_name):
            await self.client.create_collection(
                collection_name=self.fact_corpus_name,
                vectors_config=qmodels.VectorParams(size=1024, distance=qmodels.Distance.COSINE),
            )
        # Claim Archive
        if not await self.client.collection_exists(self.claim_archive_name):
            await self.client.create_collection(
                collection_name=self.claim_archive_name,
                vectors_config=qmodels.VectorParams(size=1024, distance=qmodels.Distance.COSINE),
            )
        # Image Hashes (CLIP)
        if not await self.client.collection_exists(self.image_hashes_name):
            await self.client.create_collection(
                collection_name=self.image_hashes_name,
                vectors_config=qmodels.VectorParams(size=768, distance=qmodels.Distance.COSINE),
            )

qdrant_service = QdrantService()
