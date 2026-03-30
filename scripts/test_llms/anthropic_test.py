import os
import httpx

# Set your API Key here or through environment variable
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "your-key-here")

def test_anthropic_connectivity():
    print("--- Anthropic Connectivity Test ---")
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    data = {
        "model": "claude-3-haiku-20240307",
        "max_tokens": 20,
        "messages": [
            {"role": "user", "content": "Hello! Respond with 'Connected successfully'."}
        ]
    }

    try:
        with httpx.Client() as client:
            resp = client.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=data,
                timeout=15.0
            )
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"\nResponse from AI: '{result['content'][0]['text'].strip()}'")
                print("\n✅ Verification SUCCESSFUL")
            else:
                print(f"\n❌ Verification FAILED (HTTP {resp.status_code})")
                print(f"Error: {resp.text}")
                
    except Exception as e:
        print(f"\n❌ Verification FAILED: {str(e)}")

if __name__ == "__main__":
    if ANTHROPIC_API_KEY == "your-key-here":
        print("Please set your ANTHROPIC_API_KEY in the script first.")
    else:
        test_anthropic_connectivity()
