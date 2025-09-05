import json

import requests


class OllamaClient:
    def __init__(self, host="192.168.3.70", port=11434):
        self.base_url = f"http://{host}:{port}"

    def generate_response(self, prompt, model="hf.co/unsloth/gemma-3-270m-it-GGUF:F16"):
        """
        Generate a response from the LLM using Ollama
        """
        url = f"{self.base_url}/api/generate"

        payload = {"model": model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")

        except requests.exceptions.RequestException as e:
            print(f"Error connecting to Ollama: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error parsing response: {e}")
            return None


def main():
    # Initialize the client
    client = OllamaClient()

    print("LLM Interaction with Ollama")
    print("=" * 40)

    while True:
        # Get user input
        prompt = input("\nEnter your prompt (or 'quit' to exit): ")

        if prompt.lower() in ["quit", "exit"]:
            print("Goodbye!")
            break

        if not prompt.strip():
            print("Please enter a valid prompt.")
            continue

        # Generate response
        print("Generating response...")
        response = client.generate_response(prompt)

        if response:
            print("\nResponse:")
            print("-" * 40)
            print(response)
        else:
            print("Failed to get response from LLM.")


if __name__ == "__main__":
    main()
