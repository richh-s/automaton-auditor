import fitz  # PyMuPDF
from typing import List, Dict, Optional, Any
from pydantic import BaseModel

class DocEvidence(BaseModel):
    chunk_id: str
    page_number: int
    content: str
    confidence: float
    metadata: Dict[str, Any] = {}

class DocTools:
    @staticmethod
    def ingest_pdf(path: str) -> List[DocEvidence]:
        """
        Chunks PDF by page and performs basic text extraction.
        Preserves citations (page numbers).
        """
        chunks = []
        try:
            doc = fitz.open(path)
            for page_num, page in enumerate(doc):
                text = page.get_text()
                if text.strip():
                    chunks.append(DocEvidence(
                        chunk_id=f"p{page_num + 1}",
                        page_number=page_num + 1,
                        content=text.strip(),
                        confidence=0.85, # Base ingestion confidence
                        metadata={"total_pages": len(doc)}
                    ))
            doc.close()
        except Exception as e:
            print(f"Error ingesting PDF: {e}")
            
        return chunks

    @staticmethod
    def rag_lite_query(query: str, chunks: List[DocEvidence]) -> List[DocEvidence]:
        """
        Simple keyword-based RAG-lite retrieval.
        Returns top relevant chunks with adjusted confidence.
        """
        query_terms = set(query.lower().split())
        results = []
        
        for chunk in chunks:
            content_lower = chunk.content.lower()
            matches = sum(1 for term in query_terms if term in content_lower)
            
            if matches > 0:
                # Adjust confidence based on keyword match density
                match_ratio = matches / len(query_terms)
                adjusted_confidence = min(0.85, 0.6 + (0.25 * match_ratio))
                
                results.append(DocEvidence(
                    chunk_id=chunk.chunk_id,
                    page_number=chunk.page_number,
                    content=chunk.content,
                    confidence=adjusted_confidence,
                    metadata=chunk.metadata
                ))
        
        # Sort by confidence descending
        results.sort(key=lambda x: x.confidence, reverse=True)
        return results[:3] # Return top 3 chunks
