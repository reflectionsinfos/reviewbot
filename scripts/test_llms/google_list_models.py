import httpx
from dotenv import load_dotenv

# Load local .env from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Set your API Key here or through environment variable
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

def list_google_models():
    print("--- Google Gemini Model Explorer ---")
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GOOGLE_API_KEY}"
    
    try:
        with httpx.Client() as client:
            resp = client.get(url, timeout=15.0)
            
            if resp.status_code == 200:
                result = resp.json()
                models = result.get("models", [])
                print(f"Available Models ({len(models)}):")
                for m in models:
                    name = m.get("name")
                    display_name = m.get("displayName")
                    methods = m.get("supportedGenerationMethods", [])
                    print(f" - ID: {name}")
                    print(f"   Display: {display_name}")
                    print(f"   Methods: {', '.join(methods)}")
                    print("-" * 30)
                
                print("\nListing SUCCESSFUL")
            else:
                print(f"\nFAILED (HTTP {resp.status_code})")
                print(f"Error: {resp.text}")
                
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    list_google_models()
