import httpx
from dotenv import load_dotenv

# Load local .env from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Set your API Key here or through environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def test_google_connectivity():
    print("--- Google Gemini Connectivity Test ---")
    # Using your confirmed models/ prefix
    model_name = "models/gemini-flash-latest" 
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={GOOGLE_API_KEY}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts":[{"text": "Hello! Respond with 'Connected successfully'."}]
        }],
        "generationConfig": {
            "maxOutputTokens": 20
        }
    }

    try:
        with httpx.Client() as client:
            resp = client.post(
                url,
                headers=headers,
                json=data,
                timeout=15.0
            )
            
            if resp.status_code == 200:
                result = resp.json()
                response_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                print(f"\nResponse from AI: '{response_text}'")
                print("\nVerification SUCCESSFUL")
            else:
                print(f"\nVerification FAILED (HTTP {resp.status_code})")
                print(f"Error: {resp.text}")
                
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    if GOOGLE_API_KEY == "your-key-here":
        print("Please set your GOOGLE_API_KEY in the script first.")
    else:
        test_google_connectivity()
