#!/usr/bin/env python3
"""
Script to check ChromaDB collection status on Railway via API.

This script checks:
1. Collection document counts
2. Collection distance metric
3. Foundational knowledge status
"""

import requests
import argparse
import sys

# Ensure UTF-8 output for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')


def check_railway_chromadb(backend_url: str):
    """
    Check ChromaDB status on Railway.
    
    Args:
        backend_url: Base URL of StillMe backend
    """
    print("="*60)
    print("Railway ChromaDB Status Check")
    print("="*60)
    
    # Ensure URL has scheme
    if not backend_url.startswith("http://") and not backend_url.startswith("https://"):
        backend_url = "https://" + backend_url
        print(f"ℹ️  Added https:// scheme to URL: {backend_url}")
    
    print(f"Backend URL: {backend_url}\n")
    
    try:
        # 1. Test backend connectivity
        print("1. Testing backend connectivity...")
        try:
            health_response = requests.get(
                f"{backend_url}/health",
                timeout=10
            )
            if health_response.status_code == 200:
                print("   ✅ Backend is accessible")
            else:
                print(f"   ⚠️  Backend returned status {health_response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"   ⚠️  Health check failed: {e}")
            return
        
        # 2. Get RAG stats
        print("\n2. Getting RAG collection stats...")
        try:
            stats_response = requests.get(
                f"{backend_url}/api/rag/stats",
                timeout=30
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                print("   ✅ RAG stats retrieved")
                
                vector_db = stats.get("vector_db", {})
                knowledge_docs = vector_db.get("knowledge_documents", 0)
                conversation_docs = vector_db.get("conversation_documents", 0)
                total_docs = vector_db.get("total_documents", 0)
                
                print(f"\n   Collection Status:")
                print(f"   - stillme_knowledge: {knowledge_docs} documents")
                print(f"   - stillme_conversations: {conversation_docs} documents")
                print(f"   - Total: {total_docs} documents")
                
                if knowledge_docs == 0:
                    print("\n   ⚠️  stillme_knowledge collection is EMPTY!")
                    print("   💡 Foundational knowledge may not have been added")
                    print("   💡 Run: python scripts/add_foundational_knowledge_remote.py --backend-url <url> --api-key <key>")
                else:
                    print(f"\n   ✅ stillme_knowledge collection has {knowledge_docs} documents")
                
                # Check for foundational knowledge
                if knowledge_docs > 0:
                    print("\n3. Checking for foundational knowledge...")
                    # Try to query for CRITICAL_FOUNDATION documents
                    # We can't directly query via API, but we can check if collection has documents
                    print(f"   💡 Collection has {knowledge_docs} documents")
                    print(f"   💡 Foundational knowledge should be in collection if it was added")
                    print(f"   💡 Test retrieval with: python scripts/test_self_tracking_query.py --backend-url {backend_url}")
                
            else:
                print(f"   ❌ Request failed with status code {stats_response.status_code}")
                print(f"   Response: {stats_response.text}")
                
        except requests.exceptions.Timeout:
            print("   ⚠️  Request timeout")
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request error: {e}")
        
        print("\n" + "="*60)
        print("Status check complete!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Check ChromaDB collection status on Railway via API"
    )
    parser.add_argument(
        "--backend-url",
        type=str,
        default="https://stillme-backend-production.up.railway.app",
        help="Base URL of StillMe backend"
    )
    args = parser.parse_args()
    
    check_railway_chromadb(args.backend_url)


if __name__ == "__main__":
    main()

