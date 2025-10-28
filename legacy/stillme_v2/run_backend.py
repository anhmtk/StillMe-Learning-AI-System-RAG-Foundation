#!/usr/bin/env python3
"""
Simple Backend Starter
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Start backend server"""
    try:
        print("Starting StillMe V2 Backend...")
        
        # Import and start
        import uvicorn
        from backend.api.main import app
        
        print("Backend imports successful!")
        print("Starting server on http://127.0.0.1:8000")
        
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()