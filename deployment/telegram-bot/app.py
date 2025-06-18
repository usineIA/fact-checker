import threading
import gradio as gr
from fact_check import main as run_telegram_bot, chat_with_ai

class BotManager:
    def __init__(self):
        self.status = "🔴 Arrêté"
        self.thread = None

    def start_bot(self):
        if self.thread and self.thread.is_alive():
            return "⚠️ Bot déjà en cours d'exécution"
        
        self.thread = threading.Thread(target=run_telegram_bot, daemon=True)
        self.thread.start()
        self.status = "✅ Bot Telegram actif"
        return self.status

    def get_status(self):
        return self.status

# Interface Gradio améliorée
with gr.Blocks(title="FactCheck Bot Pro") as demo:
    bot_manager = BotManager()
    
    # Section Configuration
    with gr.Row():
        gr.Markdown("## 🤖 FactCheck Bot - Version Multicanale")
    
    # Section Telegram
    with gr.Tab("Telegram Bot"):
        gr.Markdown("### Contrôle du Bot Telegram")
        status_display = gr.Textbox(label="Statut", interactive=False)
        start_btn = gr.Button("Démarrer le Bot Telegram")
        
        start_btn.click(
            fn=bot_manager.start_bot,
            outputs=status_display
        )
    
    # Section Test Direct
    with gr.Tab("Test Direct"):
        gr.Markdown("### Tester directement l'IA")
        with gr.Row():
            age_group = gr.Radio(
                choices=["enfant", "ado", "adulte"],
                label="Groupe d'âge",
                value="adulte"
            )
            user_input = gr.Textbox(label="Entrez une information à vérifier")
        
        output = gr.Textbox(label="Résultat")
        test_btn = gr.Button("Vérifier")
        
        test_btn.click(
            fn=lambda x, a: chat_with_ai(x, "Utilisateur Web", a),
            inputs=[user_input, age_group],
            outputs=output
        )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)