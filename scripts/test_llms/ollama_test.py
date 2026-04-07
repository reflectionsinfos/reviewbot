import os
import shutil
import subprocess

from dotenv import load_dotenv
from openai import OpenAI


# Load local .env from current directory
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
OLLAMA_TEST_MODELS = [
    model.strip()
    for model in os.getenv("OLLAMA_TEST_MODELS", "llama3.2:3b,gemma3:4b").split(",")
    if model.strip()
]
OLLAMA_TEST_PROMPT = os.getenv(
    "OLLAMA_TEST_PROMPT",
    "Hi! Please reply with one short sentence confirming local connectivity.",
)


def _find_ollama_binary():
    cli = shutil.which("ollama")
    if cli:
        return cli

    local_app = os.getenv("LOCALAPPDATA", "")
    if local_app:
        candidate = os.path.join(local_app, "Programs", "Ollama", "ollama.exe")
        if os.path.exists(candidate):
            return candidate
    return None


def _stop_model(model_name: str):
    ollama_bin = _find_ollama_binary()
    if not ollama_bin:
        return
    try:
        subprocess.run(
            [ollama_bin, "stop", model_name],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )
    except Exception:
        pass


def test_ollama_connectivity():
    client = OpenAI(
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
    )

    print("--- Ollama Connectivity Test ---")
    print(f"Base URL: {OLLAMA_BASE_URL}")
    try:
        print("Fetching available local models...")
        models_resp = client.models.list()
        available_models = [m.id for m in models_resp.data]
        print(f"Available models ({len(available_models)}):")
        for model_id in available_models:
            print(f" - {model_id}")

        if not available_models:
            print("No local models found.")
            print(f"Run: ollama pull {OLLAMA_TEST_MODELS[0]}")
            return

        print("\nRunning prompt tests...")
        print(f"Prompt: {OLLAMA_TEST_PROMPT}")

        overall_success = True
        for model_to_test in OLLAMA_TEST_MODELS:
            print(f"\nTesting model: {model_to_test}")
            if model_to_test not in available_models:
                print(f"Skipped: model is not installed. Run: ollama pull {model_to_test}")
                overall_success = False
                continue

            try:
                completion = client.chat.completions.create(
                    model=model_to_test,
                    messages=[
                        {
                            "role": "user",
                            "content": OLLAMA_TEST_PROMPT,
                        }
                    ],
                    max_tokens=40,
                    extra_body={"keep_alive": "0s"},
                )
                response_text = completion.choices[0].message.content.strip()
                print(f"Response from {model_to_test}: '{response_text}'")
            except Exception as model_exc:
                overall_success = False
                print(f"FAILED for {model_to_test}: {model_exc}")
            finally:
                _stop_model(model_to_test)

        if overall_success:
            print("\nVerification SUCCESSFUL")
        else:
            print("\nVerification COMPLETED with one or more failures")
    except Exception as exc:
        print(f"\nVerification FAILED: {exc}")


if __name__ == "__main__":
    test_ollama_connectivity()
