"""
Basic tests for RAG system
Critical path testing only
"""

import pytest
from backend.vector_db import ChromaClient, EmbeddingService, RAGRetrieval

def test_chroma_client_init():
    """Test ChromaDB client initialization"""
    client = ChromaClient()
    assert client is not None
    assert client.knowledge_collection is not None
    assert client.conversation_collection is not None

def test_embedding_service():
    """Test embedding service"""
    service = EmbeddingService()
    embedding = service.encode_text("test text")
    assert embedding is not None
    assert len(embedding) > 0

def test_rag_add_knowledge():
    """Test adding knowledge to RAG"""
    client = ChromaClient()
    embedding = EmbeddingService()
    rag = RAGRetrieval(client, embedding)
    
    success = rag.add_learning_content(
        content="Test knowledge",
        source="test",
        content_type="knowledge"
    )
    
    assert success is True

def test_rag_query():
    """Test RAG query retrieval"""
    client = ChromaClient()
    embedding = EmbeddingService()
    rag = RAGRetrieval(client, embedding)
    
    # Add test knowledge first
    rag.add_learning_content(
        content="StillMe is a transparent AI system",
        source="test",
        content_type="knowledge"
    )
    
    # Query
    context = rag.retrieve_context("What is StillMe?")
    assert context is not None
    assert "total_context_docs" in context

