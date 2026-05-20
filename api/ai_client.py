# api/ai_client.py
# Client OpenAI centralisé — instancié une seule fois, importé partout
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_api_key = os.getenv("OPENAI_API_KEY")
if not _api_key:
    raise ValueError("OPENAI_API_KEY est absente du fichier .env")

client = OpenAI(api_key=_api_key)
