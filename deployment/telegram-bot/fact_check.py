# Bot version enrichie avec gestion prénom/âge - Hugging Face Spaces (Gradio)
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import threading
import gradio as gr

# Récupération des tokens depuis les variables d'environnement Hugging Face
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
            return "⛔ Cette question n'est pas adaptée aux enfants. Tu peux demander à un adulte de t'aider."

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
            f"Tu expliques brièvement, de manière neutre, sans inventer de faits. Dis-le si tu n'es pas sûr(e)."
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
        return f"Une erreur s'est produite : {e}"

# Commande /start → démarrage personnalisé
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {"step": "awaiting_name"}
    await update.message.reply_text("Bonjour 👋 ! Comment t'appelles-tu ?")

# Message handler complet (avec état utilisateur)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.text.strip()

    if chat_id not in user_data:
        user_data[chat_id] = {"step": "awaiting_name"}
        await update.message.reply_text("Bonjour 👋 ! Comment t'appelles-tu ?")
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
            await update.message.reply_text("Peux-tu m'indiquer ton âge en nombre ? (ex : 10)")
        return

    elif state == "ready":
        name = user_data[chat_id]["name"]
        niveau = user_data[chat_id]["niveau"]
        response = chat_with_ai(message, name, niveau)
        await update.message.reply_text(response)

# Variable globale pour suivre le statut du bot
bot_status = {"running": False, "message": "Bot non démarré"}

def run_telegram_bot():
    """Fonction pour exécuter le bot Telegram"""
    global bot_status
    try:
        if not TELEGRAM_BOT_TOKEN:
            bot_status["message"] = "❌ Token Telegram manquant"
            return
        
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        bot_status["running"] = True
        bot_status["message"] = "✅ Bot Telegram actif et en fonctionnement"
        print("🤖 Bot lancé sur Hugging Face Spaces")
        
        application.run_polling()
    except Exception as e:
        bot_status["message"] = f"❌ Erreur bot: {str(e)}"
        print(f"Erreur bot: {e}")

def get_bot_status():
    """Fonction pour l'interface Gradio"""
    return bot_status["message"]

# Démarrage automatique du bot en arrière-plan
def start_bot_background():
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()

# Interface Gradio
demo = gr.Interface(
    fn=get_bot_status,
    inputs=None,
    outputs=gr.Textbox(label="Statut du Bot", lines=2),
    title="🤖 FactCheck Bot - Telegram",
    description="Bot Telegram de vérification d'informations adapté à l'âge. Le bot fonctionne en arrière-plan.",
    article="Utilisez votre bot sur Telegram avec la commande /start",
    allow_flagging="never"
)

if __name__ == "__main__":
    # Démarrer le bot Telegram en arrière-plan
    start_bot_background()
    
    # Lancer l'interface Gradio
    demo.launch()