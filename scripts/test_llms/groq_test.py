import os
from openai import OpenAI
from dotenv import load_dotenv

# Load local .env from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Set your key here or through environment variable
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def test_groq_connectivity():
    client = OpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=GROQ_API_KEY
    )

    print("--- Groq Connectivity Test ---")
    try:
        # First, try to list models to see which ones are available
        print("Fetching available models...")
        models_resp = client.models.list()
        available_models = [m.id for m in models_resp.data]
        print(f"Available models ({len(available_models)}):")
        for m_id in available_models:
            print(f" - {m_id}")
            
        print("\nAttempting chat completion with first available model...")
        if not available_models:
            print("No models found!")
            return

        model_to_test = available_models[0]
        # Common ones often used: llama-3.3-70b-versatile, llama3-8b-8192
        # If llama-3.3-70b-versatile is in the list, use it
        if "llama-3.3-70b-versatile" in available_models:
            model_to_test = "llama-3.3-70b-versatile"

        print(f"Testing with model: {model_to_test}")
        
        completion = client.chat.completions.create(
            model=model_to_test,
            messages=[
                {"role": "user", "content": "Hello! Respond with 'Connected successfully' if you receive this message."}
            ],
            max_tokens=20
        )
        
        print(f"\nResponse from AI: '{completion.choices[0].message.content.strip()}'")
        print("\n✅ Verification SUCCESSFUL")
    except Exception as e:
        print(f"\n❌ Verification FAILED: {str(e)}")

if __name__ == "__main__":
    test_groq_connectivity()
