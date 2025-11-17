"""
RAG Knowledge Inspector
Kiểm tra chất lượng kiến thức trong RAG database:
- Duplicate detection (trùng lặp)
- Contradiction detection (mâu thuẫn)
- Quality metrics (chất lượng)
- Statistics (thống kê)
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.vector_db.chroma_client import ChromaClient
from backend.vector_db.embeddings import EmbeddingService
from typing import List, Dict, Any
from collections import defaultdict
import hashlib
import re

def get_content_hash(content: str) -> str:
    """Generate hash for content to detect duplicates"""
    # Normalize: lowercase, remove extra whitespace
    normalized = re.sub(r'\s+', ' ', content.lower().strip())
    return hashlib.md5(normalized.encode()).hexdigest()

def detect_duplicates(documents: List[Dict[str, Any]]) -> Dict[str, List[Dict]]:
    """Detect duplicate documents based on content hash"""
    content_map = defaultdict(list)
    
    for doc in documents:
        content = doc.get("content", "")
        if content:
            content_hash = get_content_hash(content)
            content_map[content_hash].append({
                "id": doc.get("id", "unknown"),
                "content": content[:200] + "..." if len(content) > 200 else content,
                "metadata": doc.get("metadata", {}),
                "source": doc.get("metadata", {}).get("source", "unknown")
            })
    
    # Filter to only duplicates (more than 1 occurrence)
    duplicates = {k: v for k, v in content_map.items() if len(v) > 1}
    return duplicates

def detect_contradictions(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect potential contradictions (same topic, different facts)"""
    # Group by topic keywords
    topic_groups = defaultdict(list)
    
    # Extract topics from metadata or content
    for doc in documents:
        metadata = doc.get("metadata", {})
        content = doc.get("content", "")
        
        # Try to extract topic from metadata
        topic = (
            metadata.get("title", "") or
            metadata.get("topic", "") or
            metadata.get("source", "") or
            content[:50]  # First 50 chars as fallback
        )
        
        if topic:
            topic_groups[topic].append({
                "id": doc.get("id", "unknown"),
                "content": content[:300] + "..." if len(content) > 300 else content,
                "metadata": metadata
            })
    
    # Find topics with multiple documents (potential contradictions)
    contradictions = []
    for topic, docs in topic_groups.items():
        if len(docs) > 1:
            # Check for conflicting information (simplified - can be enhanced)
            contradictions.append({
                "topic": topic,
                "documents": docs,
                "count": len(docs)
            })
    
    return contradictions

def calculate_quality_metrics(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate quality metrics for documents"""
    if not documents:
        return {}
    
    lengths = [len(doc.get("content", "")) for doc in documents]
    has_metadata = sum(1 for doc in documents if doc.get("metadata"))
    has_source = sum(1 for doc in documents if doc.get("metadata", {}).get("source"))
    
    return {
        "total_documents": len(documents),
        "avg_length": sum(lengths) / len(lengths) if lengths else 0,
        "min_length": min(lengths) if lengths else 0,
        "max_length": max(lengths) if lengths else 0,
        "has_metadata": has_metadata,
        "has_source": has_source,
        "metadata_coverage": (has_metadata / len(documents) * 100) if documents else 0,
        "source_coverage": (has_source / len(documents) * 100) if documents else 0
    }

def inspect_rag_knowledge():
    """Main inspection function"""
    print("🔍 StillMe RAG Knowledge Inspector")
    print("=" * 60)
    
    try:
        # Initialize ChromaDB client
        chroma_client = ChromaClient()
        embedding_service = EmbeddingService()
        
        print("\n📊 Step 1: Retrieving all knowledge documents...")
        
        # Get all documents from knowledge collection
        # ChromaDB collection has a .get() method that can retrieve all documents
        all_documents = []
        try:
            # Access the collection directly
            knowledge_collection = chroma_client.knowledge_collection
            
            # Use .get() with no filters to get all documents
            # Limit to 10000 to avoid memory issues
            result = knowledge_collection.get(limit=10000)
            
            # Convert ChromaDB format to our document format
            if result and result.get("ids"):
                ids = result.get("ids", [])
                documents = result.get("documents", [])
                metadatas = result.get("metadatas", [])
                
                for i, doc_id in enumerate(ids):
                    all_documents.append({
                        "id": doc_id,
                        "content": documents[i] if i < len(documents) else "",
                        "metadata": metadatas[i] if i < len(metadatas) else {}
                    })
            
            print(f"✅ Retrieved {len(all_documents)} documents")
        except Exception as e:
            print(f"⚠️ Error retrieving documents: {e}")
            print("💡 Trying alternative method: broad semantic search...")
            try:
                # Fallback: Use broad semantic search
                query_embedding = embedding_service.encode_text("knowledge information data document")
                results = chroma_client.search_knowledge(
                    query_embedding=query_embedding,
                    limit=1000
                )
                all_documents = results
                print(f"✅ Retrieved {len(all_documents)} documents (via semantic search)")
            except Exception as e2:
                print(f"❌ Both methods failed: {e2}")
                print("💡 Note: You may need to use ChromaDB admin tools or check database connection.")
                return
        
        if not all_documents:
            print("⚠️ No documents found in RAG database")
            return
        
        print("\n📈 Step 2: Calculating quality metrics...")
        quality_metrics = calculate_quality_metrics(all_documents)
        print(f"   Total Documents: {quality_metrics['total_documents']}")
        print(f"   Average Length: {quality_metrics['avg_length']:.0f} characters")
        print(f"   Min Length: {quality_metrics['min_length']} characters")
        print(f"   Max Length: {quality_metrics['max_length']} characters")
        print(f"   Metadata Coverage: {quality_metrics['metadata_coverage']:.1f}%")
        print(f"   Source Coverage: {quality_metrics['source_coverage']:.1f}%")
        
        print("\n🔍 Step 3: Detecting duplicates...")
        duplicates = detect_duplicates(all_documents)
        if duplicates:
            print(f"⚠️ Found {len(duplicates)} duplicate content groups:")
            for i, (hash_val, docs) in enumerate(duplicates.items(), 1):
                print(f"\n   Duplicate Group {i} ({len(docs)} occurrences):")
                for doc in docs[:3]:  # Show first 3
                    print(f"      - ID: {doc['id']}")
                    print(f"        Source: {doc['source']}")
                    print(f"        Preview: {doc['content'][:100]}...")
                if len(docs) > 3:
                    print(f"      ... and {len(docs) - 3} more")
        else:
            print("✅ No duplicates found")
        
        print("\n⚠️ Step 4: Detecting potential contradictions...")
        contradictions = detect_contradictions(all_documents)
        if contradictions:
            print(f"⚠️ Found {len(contradictions)} topics with multiple documents (potential contradictions):")
            for i, contradiction in enumerate(contradictions[:5], 1):  # Show first 5
                print(f"\n   Topic {i}: {contradiction['topic'][:50]}")
                print(f"      Documents: {contradiction['count']}")
                for doc in contradiction['documents'][:2]:  # Show first 2
                    print(f"      - ID: {doc['id']}")
                    print(f"        Preview: {doc['content'][:100]}...")
        else:
            print("✅ No obvious contradictions detected")
        
        print("\n📋 Step 5: Source distribution...")
        source_counts = defaultdict(int)
        for doc in all_documents:
            source = doc.get("metadata", {}).get("source", "unknown")
            source_counts[source] += 1
        
        print("   Source distribution:")
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / len(all_documents) * 100) if all_documents else 0
            print(f"      {source}: {count} ({percentage:.1f}%)")
        
        print("\n" + "=" * 60)
        print("✅ Inspection complete!")
        print("\n💡 Recommendations:")
        if duplicates:
            print("   - Consider removing duplicate documents to reduce confusion")
        if contradictions:
            print("   - Review contradictory documents and consolidate if needed")
        if quality_metrics['source_coverage'] < 80:
            print("   - Improve source metadata coverage for better traceability")
        if quality_metrics['avg_length'] < 100:
            print("   - Some documents may be too short - consider enriching content")
        
    except Exception as e:
        print(f"❌ Error during inspection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_rag_knowledge()

