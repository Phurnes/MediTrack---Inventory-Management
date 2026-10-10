
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

# Load the .env file from the backend directory.
env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY is missing from .env")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model="gemini-flash-latest",
    contents="Reply with exactly: MediTrack AI testing connected",
)

print(response.text)
