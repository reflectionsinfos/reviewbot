import os
from openai import OpenAI
from dotenv import load_dotenv

# Load local .env from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Set your API Key here or through environment variable
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def test_openai_connectivity():
    client = OpenAI(api_key=OPENAI_API_KEY)

    print("--- OpenAI Connectivity Test ---")
    try:
        models_resp = client.models.list()
        available_models = [m.id for m in models_resp.data if "gpt" in m.id]
        print(f"Available GPT models ({len(available_models)}):")
        for m_id in available_models:
            print(f" - {m_id}")
            
        model_to_test = "gpt-4o-mini" # Low cost default
        print(f"\nTesting with model: {model_to_test}")
        
        completion = client.chat.completions.create(
            model=model_to_test,
            messages=[
                {"role": "user", "content": "Hello! Respond with 'Connected successfully'."}
            ],
            max_tokens=10
        )
        
        print(f"\nResponse from AI: '{completion.choices[0].message.content.strip()}'")
        print("\nVerification SUCCESSFUL")
    except Exception as e:
        print(f"\nVerification FAILED: {str(e)}")

if __name__ == "__main__":
    if OPENAI_API_KEY == "your-key-here":
        print("Please set your OPENAI_API_KEY in the script first.")
    else:
        test_openai_connectivity()
