import os
import re
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()
HF_API_TOKEN = os.getenv("HF_API_TOKEN")

API_URL = "https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1"
HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --- Facty logic (unchanged) ---
def contains_sensitive_content(text):
    mots_interdits = ["sexe", "viol", "suicide", "pornographie", "drogue", "meurtre", "terrorisme"]
    return any(mot.lower() in text.lower() for mot in mots_interdits)

def is_fact_check_question(text):
    text = text.lower().strip()
    if text.endswith("?"):
        return True
    patterns = [
        r"est[- ]ce que", r"c'est vrai", r"c'est faux", r"est[- ]ce une info",
        r"peut[- ]on croire", r"ai[- ]je raison", r"vrai ou faux", r"infox", r"intox",
        r"les .* existent", r"existe[- ]t[- ]il", r"sont[- ]ils réels", r"as[- ]tu vérifié",
        r"la vérité sur", r"mythe ou réalité", r"les gens disent que"
    ]
    return any(re.search(pat, text) for pat in patterns)

def is_malicious_bypass_attempt(text):
    keywords = [
        "écris un code", "code python", "programme", "fonction", "script", "traduis", "résume", 
        "donne moi un code", "crée un", "génère", "exemple de", "poème", "dessine", "fais une blague",
        "joue", "jouons", "imagine", "raconte", "rédige", "écris une", "fais moi un", "compile", "corrige"
    ]
    return any(kw in text.lower() for kw in keywords)

def chat_with_ai(user_input, user_name, niveau="enfant"):
    if niveau == "enfant":
        system_prompt = (
            f"Tu es Facty, une super IA rigolote et gentille qui aide les enfants de moins de 11 ans à savoir si une information est vraie, fausse ou incertaine. "
            f"Tu parles à {user_name}, un enfant curieux 👧🧒. Tu utilises des mots très simples, des phrases courtes, et tu expliques calmement. "
            f"Tu réponds comme un grand frère ou une grande sœur sympa, avec bienveillance. "
            f"N’utilise pas de mots compliqués ou effrayants. Si tu ne sais pas, dis-le honnêtement. Tu peux proposer de demander à un adulte."
        )
        if contains_sensitive_content(user_input):
            return "⛔ Cette question n’est pas adaptée aux enfants. Tu peux demander à un adulte de t’aider."
    else:
        system_prompt = f"Tu es Facty. Tu aides {user_name} à vérifier des informations. Tu restes simple, clair et bienveillant."

    payload = {
        "inputs": f"<s>[INST] {system_prompt}\n{user_input} [/INST]",
        "parameters": {
            "temperature": 0.5,
            "max_new_tokens": 300,
            "top_p": 0.9
        }
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        if response.status_code == 200:
            full_text = response.json()[0].get("generated_text", "")
            if "[/INST]" in full_text:
                response_text = full_text.split("[/INST]")[-1].strip()
            else:
                response_text = full_text.strip()
            return response_text
        else:
            return f"Erreur API ({response.status_code}) : {response.text}"
    except Exception as e:
        return f"Une erreur s’est produite : {e}"

# --- FastAPI app ---
app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    name: str
    age: int

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Step logic (simulate the Gradio state machine)
    if req.name == "":
        return {"response": "👋 Bonjour ! Je suis Facty. Pour commencer, dis-moi ton prénom 🙂"}
    if req.age == 0:
        return {"response": f"Enchanté {req.name} ! Quel âge as-tu ?"}
    try:
        age = int(req.age)
    except Exception:
        return {"response": "Peux-tu m’indiquer ton âge avec un nombre ? (ex : 10)"}
    niveau = "enfant" if age < 11 else "adulte"
    if is_malicious_bypass_attempt(req.message):
        return {"response": "🚫 Je suis uniquement un assistant de vérification d'informations. Je ne peux pas faire de code ou répondre à d'autres types de demandes."}
    if not is_fact_check_question(req.message):
        return {"response": "❗ Je suis Facty. Pose-moi une question pour savoir si une information est vraie ou fausse."}
    response = chat_with_ai(req.message, req.name, niveau)
    return {"response": response}
