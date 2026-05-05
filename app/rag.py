from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Optional
import uuid
from app.config import QDRANT_URL, QDRANT_COLLECTION

class RAGPipeline:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.collection_name = QDRANT_COLLECTION
        self._ensure_collection()
    
    def _ensure_collection(self):
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
        except Exception as e:
            print(f"Error ensuring collection: {e}")
    
    def _get_embedding(self, text: str) -> List[float]:
        return self.embedding_model.encode(text).tolist()
    
    def add_document(self, text: str, metadata: Optional[dict] = None) -> str:
        doc_id = str(uuid.uuid4())
        embedding = self._get_embedding(text)
        
        point = PointStruct(
            id=uuid.uuid4().int >> 64,
            vector=embedding,
            payload={"text": text, "doc_id": doc_id, **(metadata or {})}
        )
        
        self.client.upsert(collection_name=self.collection_name, points=[point])
        return doc_id
    
    def search(self, query: str, top_k: int = 3) -> List[dict]:
        query_embedding = self._get_embedding(query)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=top_k
        )
        
        return [
            {"text": r.payload.get("text", ""), "score": r.score, "doc_id": r.payload.get("doc_id")}
            for r in results
        ]
    
    def add_documents_batch(self, texts: List[str], metadatas: Optional[List[dict]] = None) -> List[str]:
        if not texts:
            return []
        
        embeddings = self.embedding_model.encode(texts).tolist()
        points = []
        doc_ids = []
        
        for i, text in enumerate(texts):
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            
            point = PointStruct(
                id=uuid.uuid4().int >> 64,
                vector=embeddings[i],
                payload={"text": text, "doc_id": doc_id, **metadata}
            )
            points.append(point)
        
        if points:
            self.client.upsert(collection_name=self.collection_name, points=points)
        
        return doc_ids

rag_pipeline = RAGPipeline()
