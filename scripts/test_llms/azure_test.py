import os
from openai import AzureOpenAI

# Set your Azure credentials here
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "your-key-here")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-resource.openai.azure.com/")
AZURE_OPENAI_VERSION = "2024-02-15-preview"
AZURE_DEPLOYMENT_NAME = "gpt-4o-mini" # The name you gave your deployment

def test_azure_connectivity():
    print("--- Azure OpenAI Connectivity Test ---")
    
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )

    try:
        print(f"Testing deployment: {AZURE_DEPLOYMENT_NAME}")
        
        completion = client.chat.completions.create(
            model=AZURE_DEPLOYMENT_NAME,
            messages=[
                {"role": "user", "content": "Hello! Respond with 'Connected successfully'."}
            ],
            max_tokens=20
        )
        
        print(f"\nResponse from AI: '{completion.choices[0].message.content.strip()}'")
        print("\n✅ Verification SUCCESSFUL")
    except Exception as e:
        print(f"\n❌ Verification FAILED: {str(e)}")

if __name__ == "__main__":
    if AZURE_OPENAI_API_KEY == "your-key-here":
        print("Please set your AZURE_OPENAI_API_KEY and other details in the script first.")
    else:
        test_azure_connectivity()
