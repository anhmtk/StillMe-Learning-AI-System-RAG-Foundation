#!/usr/bin/env python3
"""
StillMe RAG Demo Script
Demonstrates Vector DB and Meta-Learning capabilities
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.vector_db import ChromaClient, EmbeddingService, RAGRetrieval
from backend.learning import KnowledgeRetention, AccuracyScorer

async def demo_rag_system():
    """Demonstrate RAG system capabilities"""
    print("StillMe RAG Demo Starting...")
    print("=" * 50)
    
    try:
        # Initialize components
        print("Initializing RAG components...")
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        rag_retrieval = RAGRetrieval(chroma_client, embedding_service)
        knowledge_retention = KnowledgeRetention()
        accuracy_scorer = AccuracyScorer()
        print("All components initialized successfully!")
        print()
        
        # Add sample knowledge
        print("Adding sample knowledge...")
        sample_knowledge = [
            {
                "content": "StillMe is a self-evolving AI system that learns from conversations and improves over time.",
                "source": "system_docs",
                "type": "knowledge"
            },
            {
                "content": "Vector databases store embeddings of text to enable semantic search and retrieval.",
                "source": "tech_docs", 
                "type": "knowledge"
            },
            {
                "content": "Meta-learning allows AI systems to learn how to learn more effectively.",
                "source": "research_papers",
                "type": "knowledge"
            },
            {
                "content": "RAG (Retrieval-Augmented Generation) combines vector search with language generation.",
                "source": "tech_docs",
                "type": "knowledge"
            }
        ]
        
        for item in sample_knowledge:
            # Add to knowledge retention
            knowledge_id = knowledge_retention.add_knowledge(
                content=item["content"],
                source=item["source"],
                knowledge_type=item["type"],
                confidence_score=0.8
            )
            
            # Add to vector database
            rag_retrieval.add_learning_content(
                content=item["content"],
                source=item["source"],
                content_type=item["type"]
            )
            
            print(f"  Added: {item['content'][:50]}...")
        
        print(f"Added {len(sample_knowledge)} knowledge items!")
        print()
        
        # Add sample conversations
        print("Adding sample conversations...")
        sample_conversations = [
            {
                "content": "User: What is StillMe? StillMe: I'm a self-evolving AI system that learns and improves over time.",
                "source": "user_chat",
                "type": "conversation"
            },
            {
                "content": "User: How does RAG work? StillMe: RAG combines vector search with language generation for better responses.",
                "source": "user_chat", 
                "type": "conversation"
            }
        ]
        
        for conv in sample_conversations:
            rag_retrieval.add_learning_content(
                content=conv["content"],
                source=conv["source"],
                content_type=conv["type"]
            )
            print(f"  Added conversation: {conv['content'][:50]}...")
        
        print(f"Added {len(sample_conversations)} conversations!")
        print()
        
        # Test RAG retrieval
        print("Testing RAG retrieval...")
        test_queries = [
            "What is StillMe?",
            "How does vector search work?",
            "What is meta-learning?",
            "Tell me about RAG"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            
            # Retrieve context
            context = rag_retrieval.retrieve_context(
                query=query,
                knowledge_limit=2,
                conversation_limit=1
            )
            
            print(f"  Retrieved {context['total_context_docs']} relevant documents")
            
            # Build prompt context
            context_text = rag_retrieval.build_prompt_context(context)
            print(f"  Context: {context_text[:200]}...")
            
            # Simulate response scoring
            mock_response = f"Based on the context, {query.lower()} involves..."
            accuracy = accuracy_scorer.score_response(
                question=query,
                actual_answer=mock_response,
                expected_answer="Sample expected answer",
                scoring_method="semantic_similarity"
            )
            print(f"  Accuracy Score: {accuracy:.3f}")
        
        print("\nRAG retrieval test completed!")
        print()
        
        # Show metrics
        print("System Metrics:")
        print("-" * 30)
        
        # Vector DB stats
        vector_stats = chroma_client.get_collection_stats()
        print(f"Vector DB Documents: {vector_stats['total_documents']}")
        
        # Retention metrics
        retention_metrics = knowledge_retention.calculate_retention_metrics()
        print(f"Knowledge Items: {retention_metrics['total_knowledge_items']}")
        print(f"Average Retention: {retention_metrics['average_retention_score']:.3f}")
        print(f"Retention Rate: {retention_metrics['retention_rate']:.3f}")
        
        # Accuracy metrics
        accuracy_metrics = accuracy_scorer.get_accuracy_metrics()
        print(f"Total Responses: {accuracy_metrics['total_responses']}")
        print(f"Average Accuracy: {accuracy_metrics['average_accuracy']:.3f}")
        print(f"Learning Trend: {accuracy_metrics['trend']}")
        
        print("\nRAG Demo completed successfully!")
        print("=" * 50)
        print("StillMe now has:")
        print("  - Vector database for semantic search")
        print("  - Knowledge retention system")
        print("  - Accuracy scoring and tracking")
        print("  - RAG-enhanced responses")
        print("  - Meta-learning capabilities")
        
    except Exception as e:
        print(f"Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(demo_rag_system())
