"""
Embedding Üretme Modülü (Aşama 4)

Fotoğraf ve metinler için embedding vektörleri üretir.
"""

from .clip_embedder import CLIPEmbedder
from .sbert_embedder import SBERTEmbedder
from .faiss_manager import FaissManager

__all__ = ['CLIPEmbedder', 'SBERTEmbedder', 'FaissManager']

