import os
import requests
import logging
import json
import re
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('factcheck_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Charger les clés depuis le .env
load_dotenv()
API_TOKEN_TOGETHER = os.getenv("API_TOKEN_TOGETHER")

API_URL = "https://api.together.xyz/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN_TOGETHER}",
    "Content-Type": "application/json"
}

# Stockage temporaire des utilisateurs (optionnel, ici stateless)
user_data = {}

class FactCheckBot:
    def __init__(self):
        self.sensitive_words = {
            "high_risk": ["sexe", "viol", "suicide", "pornographie", "meurtre", "terrorisme"],
            "medium_risk": ["drogue", "alcool", "violence", "accident"],
            "topics_needing_adult": ["politique", "économie", "guerre", "religion"]
        }

    def log_user_interaction(self, user_id: str, message: str, response: str, user_level: str):
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user_id,
            "user_level": user_level,
            "message_length": len(message),
            "response_length": len(response),
            "message": message[:100] + "..." if len(message) > 100 else message
        }
        logger.info(f"User interaction: {json.dumps(log_entry)}")

    def analyze_content_safety(self, text: str, user_level: str):
        text_lower = text.lower()
        for word in self.sensitive_words["high_risk"]:
            if word in text_lower:
                if user_level == "enfant":
                    return False, "HIGH", "⛔ Cette question n'est pas adaptée aux enfants. Tu peux demander à un adulte de t'aider."
                elif user_level == "ado":
                    return False, "HIGH", "⚠️ Ce sujet est très sensible. Il est préférable d'en parler avec un adulte de confiance."
        for word in self.sensitive_words["medium_risk"]:
            if word in text_lower:
                if user_level == "enfant":
                    return False, "MEDIUM", "⚠️ Ce sujet est compliqué pour ton âge. Demande plutôt à un adulte !"
                elif user_level == "ado":
                    return True, "MEDIUM", None
        for topic in self.sensitive_words["topics_needing_adult"]:
            if topic in text_lower and user_level == "enfant":
                return False, "SUPERVISION", "🤔 C'est un sujet d'adulte. Demande plutôt à tes parents ou ton professeur !"
        return True, "SAFE", None

    def get_optimized_prompt(self, user_name: str, user_level: str, user_age: int) -> str:
        base_identity = "Tu es DinoBot, une IA spécialisée dans la vérification d'informations."
        prompts = {
            "enfant": f"""
{base_identity}

CONTEXTE UTILISATEUR:
- Nom: {user_name}
- Âge: {user_age} ans (enfant)
- Niveau: Primaire

INSTRUCTIONS SPÉCIFIQUES:
1. Utilise un vocabulaire très simple (niveau CE1-CE2)
2. Explique avec des exemples concrets du quotidien
3. Reste toujours bienveillant et encourageant
4. Si l'information est complexe, propose de demander à un adulte
5. Utilise un ou deux émojis pour rendre la réponse plus chaleureuse
6. Limite ta réponse à 1 ou 2 phrases courtes
7. Réponds toujours en français

IMPORTANT :
- NE DONNE JAMAIS d'exemple de format, de balises, ni de texte entre crochets dans ta réponse finale.
- Ne recopie pas les mots "[Émoji] [Réponse simple] [Encouragement ou conseil]" ou tout autre exemple de format.
- Ta réponse doit être naturelle, sans structure ni balises, juste la réponse pour l'enfant.
            """,
            "ado": f"""
{base_identity}

CONTEXTE UTILISATEUR:
- Nom: {user_name}
- Âge: {user_age} ans (adolescent)
- Niveau: Collège/Lycée

INSTRUCTIONS SPÉCIFIQUES:
1. Utilise un langage simple, jamais infantilisant
2. Explique de façon claire et concise (2 phrases max)
3. Ajoute un émoji si pertinent
4. Encourage l'esprit critique
5. Si c'est trop complexe, propose de demander à un adulte
6. Réponds toujours en français

IMPORTANT :
- NE DONNE JAMAIS d'exemple de format, de balises, ni de texte entre crochets dans ta réponse finale.
- Ne recopie pas les mots "[Émoji] [Réponse simple] [Encouragement ou conseil]" ou tout autre exemple de format.
- Ta réponse doit être naturelle, sans structure ni balises, juste la réponse pour l'ado.
            """,
            "adulte": f"""
{base_identity}

CONTEXTE UTILISATEUR:
- Nom: {user_name}
- Âge: {user_age} ans (adulte)
- Niveau: Mature

INSTRUCTIONS SPÉCIFIQUES:
1. Fournis une réponse concise et factuelle (2-3 phrases max)
2. Explique ta méthodologie si pertinent, mais reste bref
3. Réponds toujours en français

IMPORTANT :
- NE DONNE JAMAIS d'exemple de format, de balises, ni de texte entre crochets dans ta réponse finale.
- Ta réponse doit être naturelle, sans structure ni balises.
            """
        }
        return prompts.get(user_level, prompts["adulte"])

    def chat_with_ai(self, user_input: str, user_name: str, user_level: str, user_age: int) -> str:
        is_safe, warning_level, safety_message = self.analyze_content_safety(user_input, user_level)
        if not is_safe:
            logger.warning(f"Unsafe content detected - Level: {warning_level}, User: {user_name} ({user_level})")
            return safety_message
        system_prompt = self.get_optimized_prompt(user_name, user_level, user_age)
        payload = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.3,
            "max_tokens": 300 if user_level != "enfant" else 200,
            "top_p": 0.85
        }
        try:
            logger.info(f"API call for user {user_name} ({user_level}): {user_input[:50]}...")
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
            if response.status_code == 200:
                ai_response = response.json()['choices'][0]['message']['content'].strip()
                logger.info(f"Successful API response for {user_name}")
                return ai_response
            else:
                logger.error(f"API Error {response.status_code}: {response.text}")
                return self.get_error_message(user_level, "api_error")
        except requests.exceptions.Timeout:
            logger.error(f"Timeout for user {user_name}")
            return self.get_error_message(user_level, "timeout")
        except Exception as e:
            logger.error(f"Unexpected error for user {user_name}: {str(e)}")
            return self.get_error_message(user_level, "general_error")

    def get_error_message(self, user_level: str, error_type: str) -> str:
        messages = {
            "enfant": {
                "api_error": "😅 Oups ! J'ai un petit problème technique. Peux-tu réessayer dans quelques minutes ?",
                "timeout": "⏰ Je réfléchis trop lentement ! Peux-tu me reposer ta question ?",
                "general_error": "🤖 J'ai un petit bug ! Essaie de me poser ta question différemment."
            },
            "ado": {
                "api_error": "⚠️ Problème technique temporaire. Réessaie dans quelques instants.",
                "timeout": "⏱️ La connexion est lente. Peux-tu reformuler ta question ?",
                "general_error": "🔧 Erreur système. Essaie avec une formulation différente."
            },
            "adulte": {
                "api_error": "Erreur API temporaire. Veuillez réessayer ultérieurement.",
                "timeout": "Délai de connexion dépassé. Reformulez votre question.",
                "general_error": "Erreur technique. Essayez une formulation alternative."
            }
        }
        return messages.get(user_level, messages["adulte"]).get(error_type, "Erreur inconnue.")

# Instance globale du bot
factcheck_bot = FactCheckBot()

# --- FastAPI app ---
app = FastAPI()

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

# --- Filtres fact-check et sécurité ---
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

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    # Logique d'accueil et de gestion du "state" utilisateur (stateless ici)
    if req.name == "":
        return {"response": "👋 Bonjour ! Je suis DinoBot. Pour commencer, dis-moi ton prénom 🙂"}
    if req.age == 0:
        return {"response": f"Enchanté {req.name} ! Quel âge as-tu ?"}
    try:
        age = int(req.age)
    except Exception:
        return {"response": "Peux-tu m’indiquer ton âge avec un nombre ? (ex : 10)"}
    if age < 11:
        niveau = "enfant"
    elif age < 15:
        niveau = "ado"
    else:
        niveau = "adulte"
    # Filtre pour éviter que l'IA réponde à un simple nombre (âge)
    if req.message.strip().isdigit() and 3 <= int(req.message.strip()) <= 120:
        return {"response": "Merci pour ton âge ! Pose-moi maintenant une question à vérifier (ex : 'Est-ce que les chats ont 9 vies ?')."}
    # Filtres fact-check et sécurité
    if is_malicious_bypass_attempt(req.message):
        return {"response": "🚫 Je suis uniquement un assistant de vérification d'informations. Je ne peux pas faire de code, de poème ou répondre à d'autres types de demandes."}
    if not is_fact_check_question(req.message):
        return {"response": "❗ Je suis DinoBot. Pose-moi une question pour savoir si une information est vraie ou fausse."}
    response = factcheck_bot.chat_with_ai(req.message, req.name, niveau, age)
    factcheck_bot.log_user_interaction(req.name, req.message, response, niveau)
    return {"response": response}
