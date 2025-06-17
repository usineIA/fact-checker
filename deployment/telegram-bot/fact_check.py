# Bot version enrichie avec gestion prénom/âge
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv

# Charger les clés depuis le .env
load_dotenv()
API_TOKEN_TOGETHER = os.getenv("API_TOKEN_TOGETHER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

API_URL = "https://api.together.xyz/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN_TOGETHER}",
    "Content-Type": "application/json"
}

# Stockage temporaire des utilisateurs
user_data = {}

def contains_sensitive_content(text):
    mots_interdits = ["sexe", "viol", "suicide", "pornographie", "drogue", "meurtre", "terrorisme"]
    return any(mot.lower() in text.lower() for mot in mots_interdits)

# Fonction de réponse IA
def chat_with_ai(user_input, user_name, niveau="enfant"):
    if niveau == "enfant":
        system_prompt = (
            f"Tu es FactCheck_Bot, une IA sympa qui aide les enfants de moins de 11 ans à savoir si une information est vraie, fausse ou incertaine. "
            f"Tu parles à {user_name} avec des mots très simples. Tu expliques calmement, sans sujets choquants. "
            f"Si tu ne sais pas, dis-le honnêtement. Propose de demander à un adulte si besoin."
        )
        if contains_sensitive_content(user_input):
            return "⛔ Cette question n’est pas adaptée aux enfants. Tu peux demander à un adulte de t’aider."

    elif niveau == "ado":
        system_prompt = (
            f"Tu es FactCheck_Bot, une IA qui aide les adolescents à comprendre si une information est vraie, fausse ou incertaine. "
            f"Tu parles à {user_name} de manière claire. Tu restes factuel et respectueux, sans contenu choquant."
        )
        if contains_sensitive_content(user_input):
            return "⚠️ Ce sujet est sensible. Tu peux en parler avec un adulte ou poser une autre question."

    else:  # adulte
        system_prompt = (
            f"Tu es FactCheck_Bot, une IA experte en vérification d'informations. "
            f"Tu aides {user_name} à savoir si une affirmation est vraie, fausse ou incertaine. "
            f"Tu expliques brièvement, de manière neutre, sans inventer de faits. Dis-le si tu n’es pas sûr(e)."
        )

    payload = {
        "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "temperature": 0.5,
        "max_tokens": 300,
        "top_p": 0.9
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content'].strip()
        else:
            return f"Erreur API ({response.status_code}) : {response.text}"
    except Exception as e:
        return f"Une erreur s’est produite : {e}"

# Commande /start → démarrage personnalisé
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {"step": "awaiting_name"}
    await update.message.reply_text("Bonjour 👋 ! Comment t’appelles-tu ?")

# Message handler complet (avec état utilisateur)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.text.strip()

    if chat_id not in user_data:
        user_data[chat_id] = {"step": "awaiting_name"}
        await update.message.reply_text("Bonjour 👋 ! Comment t’appelles-tu ?")
        return

    state = user_data[chat_id]["step"]

    if state == "awaiting_name":
        user_data[chat_id]["name"] = message
        user_data[chat_id]["step"] = "awaiting_age"
        await update.message.reply_text("Enchanté ! Quel âge as-tu ?")
        return

    elif state == "awaiting_age":
        try:
            age = int(message)
            user_data[chat_id]["age"] = age
            user_data[chat_id]["step"] = "ready"
            if age < 11:
                user_data[chat_id]["niveau"] = "enfant"
            elif age < 15:
                user_data[chat_id]["niveau"] = "ado"
            else:
                user_data[chat_id]["niveau"] = "adulte"
            await update.message.reply_text(f"Génial {user_data[chat_id]['name']} ! Je suis là pour t'aider à vérifier tes informations. Prêt ?")
        except ValueError:
            await update.message.reply_text("Peux-tu m’indiquer ton âge en nombre ? (ex : 10)")
        return

    elif state == "ready":
        name = user_data[chat_id]["name"]
        niveau = user_data[chat_id]["niveau"]
        response = chat_with_ai(message, name, niveau)
        await update.message.reply_text(response)

# Lancement du bot
def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Token Telegram manquant ou vide.")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot lancé. En attente de messages...")
    application.run_polling()

if __name__ == '__main__':
    main()