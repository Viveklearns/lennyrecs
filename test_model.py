#!/usr/bin/env python3
"""Test which Claude API model works."""

import os
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

API_KEY = os.getenv("ANTHROPIC_API_KEY")
client = Anthropic(api_key=API_KEY)

# Try different model names
models_to_try = [
    "claude-3-5-sonnet-20241022",
    "claude-3-5-sonnet-20240620",
    "claude-3-7-sonnet-20250219",
    "claude-sonnet-4-5-20250929",
    "claude-3-sonnet-20240229",
    "claude-sonnet-3.5-20240620",
]

for model in models_to_try:
    try:
        print(f"\nTrying {model}...")
        response = client.messages.create(
            model=model,
            max_tokens=50,
            messages=[{"role": "user", "content": "Say 'OK'"}]
        )
        print(f"✅ SUCCESS with {model}")
        print(f"Response: {response.content[0].text}")
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg:
            print(f"❌ Model not found")
        elif "deprecated" in error_msg.lower():
            print(f"⚠️  Model deprecated but works")
            print(f"Response: {response.content[0].text}")
            break
        else:
            print(f"❌ Error: {e}")
