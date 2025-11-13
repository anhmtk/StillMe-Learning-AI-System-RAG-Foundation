#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
View documents in ChromaDB Vector Database
Shows detailed information about knowledge and conversation documents
"""

import os
import sys
import requests
import json
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Get API base from environment or use default
# Priority: STILLME_API_BASE env var > default localhost
API_BASE = os.getenv("STILLME_API_BASE", "http://localhost:8000")
API_KEY = os.getenv("STILLME_API_KEY", "")

# If no env var set and default is localhost, show helpful message
if API_BASE == "http://localhost:8000" and not os.getenv("STILLME_API_BASE"):
    print("WARNING: No STILLME_API_BASE environment variable set.")
    print("TIP: If backend is on Railway, set it like this:")
    print("   Windows PowerShell: $env:STILLME_API_BASE='https://stillme-backend-production.up.railway.app'")
    print("   Windows CMD: set STILLME_API_BASE=https://stillme-backend-production.up.railway.app")
    print("   Linux/Mac: export STILLME_API_BASE=https://stillme-backend-production.up.railway.app")
    print()
    print("   Or run: STILLME_API_BASE=https://stillme-backend-production.up.railway.app python scripts/view_vector_db_documents.py")
    print()

def get_documents(collection="all", limit=100, offset=0):
    """Get documents from Vector DB"""
    url = f"{API_BASE}/api/rag/list-documents"
    params = {
        "collection": collection,
        "limit": limit,
        "offset": offset
    }
    headers = {}
    if API_KEY:
        headers["X-API-Key"] = API_KEY
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 401:
            print("❌ Authentication required. Set STILLME_API_KEY environment variable.")
            print(f"💡 Endpoint requires API key. Check Railway environment variables for STILLME_API_KEY")
            return None
        elif response.status_code == 404:
            print(f"❌ Endpoint not found: {url}")
            print("💡 This endpoint may not be deployed yet. Check if backend code is up to date on Railway.")
            print("💡 Try checking other endpoints like /api/rag/stats to verify backend is working.")
            return None
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {API_BASE}")
        print()
        if API_BASE == "http://localhost:8000":
            print("💡 Backend is not running on localhost:8000")
            print("💡 If backend is on Railway, set STILLME_API_BASE environment variable:")
            print("   Windows PowerShell: $env:STILLME_API_BASE='https://stillme-backend-production.up.railway.app'")
            print("   Windows CMD: set STILLME_API_BASE=https://stillme-backend-production.up.railway.app")
            print("   Linux/Mac: export STILLME_API_BASE=https://stillme-backend-production.up.railway.app")
        else:
            print(f"💡 Make sure backend is running at {API_BASE}")
            print("💡 Check Railway dashboard to ensure backend service is running")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_stats():
    """Get Vector DB statistics"""
    url = f"{API_BASE}/api/rag/stats"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json().get("stats", {})
        elif response.status_code == 404:
            print(f"⚠️  Warning: /api/rag/stats endpoint not found. Backend may be outdated.")
            return None
        else:
            print(f"⚠️  Warning: Stats endpoint returned {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        return None

def main():
    print("=" * 80)
    print("📚 StillMe Vector DB Documents Viewer")
    print("=" * 80)
    print(f"API Base: {API_BASE}")
    if API_KEY:
        print(f"API Key: {'*' * (len(API_KEY) - 4)}{API_KEY[-4:] if len(API_KEY) > 4 else '****'}")
    else:
        print("API Key: Not set (may be required for some endpoints)")
    print()
    
    # Get stats first
    stats = get_stats()
    if stats:
        print("📊 Vector DB Statistics:")
        print(f"  Total Documents: {stats.get('total_documents', 0)}")
        print(f"  Knowledge Docs: {stats.get('knowledge_documents', 0)}")
        print(f"  Conversation Docs: {stats.get('conversation_documents', 0)}")
        print()
    
    # Get documents
    print("📖 Fetching documents...")
    data = get_documents(collection="all", limit=100)
    
    if not data:
        print("❌ Failed to get documents")
        return
    
    # Display knowledge documents
    knowledge_docs = data.get("knowledge_documents", [])
    total_knowledge = data.get("total_knowledge", 0)
    
    print()
    print("=" * 80)
    print(f"📚 Knowledge Documents ({len(knowledge_docs)}/{total_knowledge} shown)")
    print("=" * 80)
    
    if knowledge_docs:
        for i, doc in enumerate(knowledge_docs, 1):
            print(f"\n[{i}] ID: {doc.get('id', 'N/A')}")
            metadata = doc.get("metadata", {})
            if metadata:
                print(f"    Source: {metadata.get('source', 'N/A')}")
                print(f"    Type: {metadata.get('type', 'N/A')}")
                if 'timestamp' in metadata:
                    print(f"    Timestamp: {metadata.get('timestamp', 'N/A')}")
                if 'title' in metadata:
                    print(f"    Title: {metadata.get('title', 'N/A')}")
            print(f"    Content Length: {doc.get('content_length', 0)} chars")
            content = doc.get("content", "")
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"    Preview: {preview}")
    else:
        print("  (No knowledge documents found)")
    
    # Display conversation documents
    conversation_docs = data.get("conversation_documents", [])
    total_conversation = data.get("total_conversation", 0)
    
    print()
    print("=" * 80)
    print(f"💬 Conversation Documents ({len(conversation_docs)}/{total_conversation} shown)")
    print("=" * 80)
    
    if conversation_docs:
        for i, doc in enumerate(conversation_docs, 1):
            print(f"\n[{i}] ID: {doc.get('id', 'N/A')}")
            metadata = doc.get("metadata", {})
            if metadata:
                print(f"    Source: {metadata.get('source', 'N/A')}")
                if 'timestamp' in metadata:
                    print(f"    Timestamp: {metadata.get('timestamp', 'N/A')}")
                if 'user_id' in metadata:
                    print(f"    User ID: {metadata.get('user_id', 'N/A')}")
            print(f"    Content Length: {doc.get('content_length', 0)} chars")
            content = doc.get("content", "")
            if content:
                preview = content[:200] + "..." if len(content) > 200 else content
                print(f"    Preview: {preview}")
    else:
        print("  (No conversation documents found)")
    
    print()
    print("=" * 80)
    print("💡 Tips:")
    print("   - Use ?collection=knowledge or ?collection=conversation to filter")
    print("   - Set STILLME_API_KEY if authentication is required")
    print("   - Set STILLME_API_BASE if backend is not on localhost:8000")
    print()
    print("⚠️  If you see 404 error:")
    print("   - Endpoint /api/rag/list-documents may not be deployed yet")
    print("   - Push latest code to Railway and redeploy backend service")
    print("   - Or check if endpoint path is correct in backend code")
    print("=" * 80)

if __name__ == "__main__":
    main()

