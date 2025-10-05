#!/usr/bin/env python3
"""
Load Ollama model
"""

import json

import requests


def load_model():
    url = "http://127.0.0.1:11434/api/generate"

    # First, try to load the model with a simple prompt
    payload = {
        "model": "gemma2:2b",
        "prompt": "Hello, I am StillMe. How can I help you?",
        "stream": False,
    }

    try:
        print("🔄 Loading Ollama model...")
        print(f"📤 Sending to: {url}")

        response = requests.post(url, json=payload, timeout=120)

        print(f"📊 Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"📄 Response: {json.dumps(data, indent=2)}")

            if data.get("response"):
                print("✅ Model loaded successfully!")
                print(f"🤖 Response: {data['response']}")
            else:
                print("❌ Model not responding properly")
        else:
            print(f"❌ Error: {response.text}")

    except Exception as e:
        print(f"❌ Exception: {e}")


if __name__ == "__main__":
    load_model()
