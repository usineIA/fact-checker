# Bot version enrichie avec debugging, tests et système d'invites optimisé
import os
import requests
import logging
import json
from datetime import datetime
from typing import Dict, Optional, Tuple
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
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
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

API_URL = "https://api.together.xyz/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {API_TOKEN_TOGETHER}",
    "Content-Type": "application/json"
}

# Stockage temporaire des utilisateurs avec structure améliorée
user_data = {}

class FactCheckBot:
    def __init__(self):
        self.sensitive_words = {
            "high_risk": ["sexe", "viol", "suicide", "pornographie", "meurtre", "terrorisme"],
            "medium_risk": ["drogue", "alcool", "violence", "accident"],
            "topics_needing_adult": ["politique", "économie", "guerre", "religion"]
        }
        
    def log_user_interaction(self, chat_id: int, message: str, response: str, user_level: str):
        """Enregistre les interactions pour le debugging"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "chat_id": chat_id,
            "user_level": user_level,
            "message_length": len(message),
            "response_length": len(response),
            "message": message[:100] + "..." if len(message) > 100 else message  # Tronquer pour la confidentialité
        }
        logger.info(f"User interaction: {json.dumps(log_entry)}")

    def analyze_content_safety(self, text: str, user_level: str) -> Tuple[bool, str, str]:
        """
        Analyse la sécurité du contenu
        Returns: (is_safe, warning_level, message)
        """
        text_lower = text.lower()
        
        # Vérification des mots à haut risque
        for word in self.sensitive_words["high_risk"]:
            if word in text_lower:
                if user_level == "enfant":
                    return False, "HIGH", "⛔ Cette question n'est pas adaptée aux enfants. Tu peux demander à un adulte de t'aider."
                elif user_level == "ado":
                    return False, "HIGH", "⚠️ Ce sujet est très sensible. Il est préférable d'en parler avec un adulte de confiance."
        
        # Vérification des mots à risque moyen
        for word in self.sensitive_words["medium_risk"]:
            if word in text_lower:
                if user_level == "enfant":
                    return False, "MEDIUM", "⚠️ Ce sujet est compliqué pour ton âge. Demande plutôt à un adulte !"
                elif user_level == "ado":
                    return True, "MEDIUM", None  # Peut être traité mais avec précaution
        
        # Sujets nécessitant supervision adulte
        for topic in self.sensitive_words["topics_needing_adult"]:
            if topic in text_lower and user_level == "enfant":
                return False, "SUPERVISION", "🤔 C'est un sujet d'adulte. Demande plutôt à tes parents ou ton professeur !"
        
        return True, "SAFE", None

    def get_optimized_prompt(self, user_name: str, user_level: str, user_age: int) -> str:
        """Génère des prompts optimisés selon le niveau utilisateur"""
        
        base_identity = "Tu es FactCheck_Bot, une IA spécialisée dans la vérification d'informations."
        
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
5. Utilise des émojis pour rendre tes réponses plus amusantes
6. Limite tes réponses à 2-3 phrases courtes
7. Répond toujours en français, en moins de 300 mots

RÈGLES DE SÉCURITÉ:
- Évite tous sujets sensibles ou effrayants
- Si tu ne peux pas répondre simplement, redirige vers un adulte
- Encourage toujours la curiosité tout en restant prudent

FORMAT DE RÉPONSE:
[Émoji] [Réponse simple] [Encouragement ou conseil]

Tu DOIS ABSOLUMENT respecter ce format exact, sans variation :

ÉMOJI + RÉPONSE + ENCOURAGEMENT

RÈGLES STRICTES :
Commence TOUJOURS par un émoji
Finis TOUJOURS par un encouragement avec émoji
Ne jamais expliquer le format
Ne jamais écrire "FORMAT DE RÉPONSE" dans ta réponse
            """,
            
            "ado": f"""
{base_identity}

CONTEXTE UTILISATEUR:
- Nom: {user_name}
- Âge: {user_age} ans (adolescent)
- Niveau: Collège/Lycée

INSTRUCTIONS SPÉCIFIQUES:
1. Utilise un langage clair mais pas infantilisant
2. Explique les sources et la méthode de vérification
3. Encourage l'esprit critique
4. Aborde les nuances sans dramatiser
5. Propose des ressources fiables pour approfondir
6. Limite à 4-5 phrases avec structure logique
7. Répond toujours en français, en moins de 300 mots

RÈGLES DE SÉCURITÉ:
- Traite les sujets sensibles avec mesure
- Encourage le dialogue avec des adultes de confiance si nécessaire
- Développe l'autonomie de réflexion

FORMAT DE RÉPONSE:
[Statut: VRAI/FAUX/INCERTAIN] [Explication] [Source/Méthode] [Conseil]
            """,
            
            "adulte": f"""
{base_identity}

CONTEXTE UTILISATEUR:
- Nom: {user_name}
- Âge: {user_age} ans (adulte)
- Niveau: Mature

INSTRUCTIONS SPÉCIFIQUES:
1. Fournis une analyse factuelle et nuancée
2. Cite tes sources et limites de connaissance
3. Explique ta méthodologie de vérification
4. Aborde les controverses de manière équilibrée
5. Suggère des vérifications croisées si pertinent
6. Sois concis mais complet (max 6-7 phrases)
7. Répond toujours en français, en moins de 300 mots

RÈGLES PROFESSIONNELLES:
- Reste objectif et neutre
- Distingue clairement faits établis, probable et incertain
- Indique tes limites de connaissance temporelle (cutoff)
- Encourage la vérification indépendante

FORMAT DE RÉPONSE:
[STATUT] [Analyse factuelle] [Sources/Limites] [Recommandations de vérification]
            """
        }
        
        return prompts.get(user_level, prompts["adulte"])

    def chat_with_ai(self, user_input: str, user_name: str, user_level: str, user_age: int) -> str:
        """Fonction de chat avec l'IA améliorée"""
        
        # Vérification de sécurité du contenu
        is_safe, warning_level, safety_message = self.analyze_content_safety(user_input, user_level)
        
        if not is_safe:
            logger.warning(f"Unsafe content detected - Level: {warning_level}, User: {user_name} ({user_level})")
            return safety_message
        
        # Génération du prompt optimisé
        system_prompt = self.get_optimized_prompt(user_name, user_level, user_age)
        
        payload = {
            "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            "temperature": 0.3,  # Réduit pour plus de cohérence
            "max_tokens": 300 if user_level != "enfant" else 200,
            "top_p": 0.85
        }
        
        try:
            logger.info(f"API call for user {user_name} ({user_level}): {user_input[:50]}...")
            response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=15)
            
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
        """Messages d'erreur adaptés au niveau utilisateur"""
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

# Commande /start → démarrage personnalisé
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {
        "step": "awaiting_name",
        "start_time": datetime.now(),
        "interactions": 0
    }
    logger.info(f"New user started: {chat_id}")
    await update.message.reply_text("Bonjour 👋 ! Je suis FactCheck_Bot. Comment t'appelles-tu ?")

# Commande /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
🤖 **FactCheck_Bot - Guide d'utilisation**

Je t'aide à vérifier si une information est vraie ou fausse !

**Commandes disponibles :**
• /start - Commencer ou recommencer
• /help - Afficher cette aide
• /stats - Voir tes statistiques
• /reset - Réinitialiser tes données

**Comment ça marche :**
1. Dis-moi ton prénom et ton âge
2. Pose-moi ta question sur une info à vérifier
3. Je t'explique si c'est vrai, faux ou incertain

**Exemples de questions :**
• "Est-ce que les chats ont 9 vies ?"
• "Les humains utilisent seulement 10% de leur cerveau ?"
• "Boire 8 verres d'eau par jour est obligatoire ?"

Prêt à débusquer les fake news ? 🕵️‍♂️
    """
    await update.message.reply_text(help_text)

# Commande /stats
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_data and "name" in user_data[chat_id]:
        data = user_data[chat_id]
        stats_text = f"""
📊 **Statistiques de {data['name']}**

• Questions posées : {data.get('interactions', 0)}
• Depuis le : {data.get('start_time', datetime.now()).strftime('%d/%m/%Y à %H:%M')}
• Niveau : {data.get('niveau', 'Non défini')}

Continue à poser des questions ! 🎯
        """
    else:
        stats_text = "📊 Aucune statistique disponible. Utilise /start d'abord !"
    
    await update.message.reply_text(stats_text)

# Commande /reset
async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_data:
        del user_data[chat_id]
        logger.info(f"User data reset for {chat_id}")
    await update.message.reply_text("🔄 Tes données ont été effacées. Utilise /start pour recommencer !")

# Message handler complet (avec état utilisateur)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    message = update.message.text.strip()

    if chat_id not in user_data:
        user_data[chat_id] = {
            "step": "awaiting_name",
            "start_time": datetime.now(),
            "interactions": 0
        }
        await update.message.reply_text("Bonjour 👋 ! Comment t'appelles-tu ?")
        return

    state = user_data[chat_id]["step"]

    if state == "awaiting_name":
        # Validation du prénom
        if len(message) > 20 or not message.replace(" ", "").replace("-", "").isalpha():
            await update.message.reply_text("🤔 Peux-tu me donner juste ton prénom ? (sans chiffres ni caractères spéciaux)")
            return
            
        user_data[chat_id]["name"] = message.title()
        user_data[chat_id]["step"] = "awaiting_age"
        logger.info(f"User {chat_id} provided name: {message}")
        await update.message.reply_text(f"Enchanté {message} ! Quel âge as-tu ?")
        return

    elif state == "awaiting_age":
        try:
            age = int(message)
            if age < 3 or age > 120:
                await update.message.reply_text("🤨 Cet âge me semble bizarre... Peux-tu me dire ton vrai âge ?")
                return
                
            user_data[chat_id]["age"] = age
            user_data[chat_id]["step"] = "ready"
            
            # Définition du niveau basé sur l'âge
            if age < 11:
                user_data[chat_id]["niveau"] = "enfant"
                welcome_msg = f"Super {user_data[chat_id]['name']} ! 🌟 Je vais t'expliquer les choses simplement. Pose-moi tes questions !"
            elif age < 15:
                user_data[chat_id]["niveau"] = "ado"
                welcome_msg = f"Parfait {user_data[chat_id]['name']} ! 🎯 Je t'aiderai à démêler le vrai du faux. Quelle info veux-tu vérifier ?"
            else:
                user_data[chat_id]["niveau"] = "adulte"
                welcome_msg = f"Bonjour {user_data[chat_id]['name']} ! 🔍 Prêt à fact-checker ensemble ? Quelle information souhaitez-vous vérifier ?"
            
            logger.info(f"User {chat_id} setup complete: {user_data[chat_id]['name']}, {age} years, level: {user_data[chat_id]['niveau']}")
            await update.message.reply_text(welcome_msg)
            
        except ValueError:
            await update.message.reply_text("🔢 Peux-tu m'indiquer ton âge en chiffres ? (par exemple : 10)")
        return

    elif state == "ready":
        # Increment interaction counter
        user_data[chat_id]["interactions"] = user_data[chat_id].get("interactions", 0) + 1
        
        name = user_data[chat_id]["name"]
        niveau = user_data[chat_id]["niveau"]
        age = user_data[chat_id]["age"]
        
        # Générer la réponse IA
        response = factcheck_bot.chat_with_ai(message, name, niveau, age)
        
        # Logger l'interaction
        factcheck_bot.log_user_interaction(chat_id, message, response, niveau)
        
        await update.message.reply_text(response)

# Gestionnaire d'erreurs
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "😅 Oups ! Une erreur s'est produite. Essaie de reformuler ta question."
        )

# Validation de la configuration
def validate_config():
    """Valide la configuration avant le lancement"""
    errors = []
    
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        errors.append("Token Telegram manquant (TELEGRAM_BOT_TOKEN)")
    
    if not os.getenv("API_TOKEN_TOGETHER"):
        errors.append("Token Together AI manquant (API_TOKEN_TOGETHER)")
    
    if errors:
        for error in errors:
            logger.error(error)
        raise ValueError(f"Configuration invalide: {', '.join(errors)}")
    
    logger.info("Configuration validée avec succès")

# Lancement du bot
def main():
    try:
        validate_config()
        
        application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Ajout des handlers
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("stats", stats_command))
        application.add_handler(CommandHandler("reset", reset_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Gestionnaire d'erreurs
        application.add_error_handler(error_handler)
        
        logger.info("🤖 FactCheck_Bot lancé avec succès. En attente de messages...")
        print("🤖 FactCheck_Bot lancé. Vérifiez factcheck_bot.log pour les détails.")
        
        # Lancement en mode polling
        application.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.critical(f"Erreur critique au lancement: {e}")
        print(f"❌ Erreur critique: {e}")
        raise

if __name__ == '__main__':
    main()