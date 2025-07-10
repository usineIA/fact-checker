"use client";
import Image from "next/image";
import { useState, useRef, useEffect } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "👋 Bonjour ! Je suis DinoBot. Pour commencer, dis-moi ton prénom 🙂",
    },
  ]);
  const [input, setInput] = useState("");
  const [step, setStep] = useState<"awaiting_name" | "awaiting_age" | "ready">(
    "awaiting_name"
  );
  const [name, setName] = useState("");
  const [age, setAge] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [year, setYear] = useState<number | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    setYear(new Date().getFullYear());
  }, []);

  const handleSend = async () => {
    if (!input.trim()) return;
    setMessages((prev) => [...prev, { role: "user", content: input }]);
    setLoading(true);
    let payload: { message: string; name: string; age: number } = { message: "", name: "", age: 0 };
    let nextStep = step;
    if (step === "awaiting_name") {
      payload = { message: input, name: input.trim(), age: 0 };
      setName(input.trim());
      nextStep = "awaiting_age";
    } else if (step === "awaiting_age") {
      const parsedAge = parseInt(input.trim());
      if (!isNaN(parsedAge)) {
        setAge(parsedAge);
        payload = { message: input, name, age: parsedAge };
        nextStep = "ready";
      } else {
        payload = { message: input, name, age: 0 };
      }
    } else if (step === "ready") {
      payload = { message: input, name, age: age ?? 0 };
    }
    setInput("");
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);
      if (data.response && data.response.includes("Quel âge as-tu")) {
        setStep("awaiting_age");
        setInput("");
      } else if (data.response && data.response.includes("Pose-moi une question")) {
        setStep("ready");
        setInput("");
      } else if (nextStep) {
        setStep(nextStep);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "❌ Erreur de connexion au serveur." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" && !loading) {
      handleSend();
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-br from-[#B6F3EF] to-[#E6D6FB] flex flex-col items-center py-4 px-2">
      <div className="w-full max-w-6xl bg-[#FEFEFD]/90 rounded-3xl shadow-xl p-4 flex flex-col items-center border-4 border-[#7840D8]">
        <Image
          src="/assets/dinobot_logo.png"
          alt="DinoBot Logo"
          width={250}
          height={250}
          className="rounded-2xl mb-2 border-4 border-[#3BCEC4] shadow-lg"
        />
        
        <p className="text-lg text-[#7840D8] font-semibold mb-4 text-center">
          🤖 Le fact-checker rigolo pour les petits (et les plus grands !) <br />Vérifie si une info est vraie ou fausse, en toute simplicité.
        </p>
        <div className="w-full flex flex-col gap-2 bg-[#9F7AF8]/10 rounded-xl p-4 h-[480px] overflow-y-auto mb-3 border-2 border-[#3BCEC4]">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <Image
                  src="/assets/dinobot_logo-2.png"
                  alt="Bot"
                  width={60}
                  height={60}
                  className="rounded-2xl border-2 border-[#FED808]"
                />
              )}
              <div
                className={`px-4 py-2 rounded-2xl max-w-[70%] text-base font-large shadow-md ${
                  msg.role === "user"
                    ? "bg-[#3BCEC4] text-[#242672] self-end"
                    : "bg-[#FEFEFD] text-[#7840D8]"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <Image
                  src="/assets/user_avatar.png"
                  alt="User"
                  width={60}
                  height={60}
                  className="rounded-2xl border-2 border-[#FED808]"
                />
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <div className="w-full flex gap-2 mt-2">
          <input
            type="text"
            className="flex-1 rounded-xl border-2 border-[#7840D8] px-4 py-2 text-lg focus:outline-none focus:ring-2 focus:ring-[#3BCEC4] bg-white text-[#242672] placeholder:text-[#9F7AF8]"
            placeholder={
              step === "awaiting_name"
                ? "Tape ton prénom ici..."
                : step === "awaiting_age"
                ? "Tape ton âge ici..."
                : "Pose ta question ici..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleInputKeyDown}
            disabled={loading}
            aria-label="Zone de saisie du chat"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="bg-[#7840D8] hover:bg-[#9F7AF8] text-white font-bold px-5 py-2 rounded-xl shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Envoyer"
          >
            {loading ? "..." : "Envoyer"}
          </button>
        </div>
      </div>
      <footer className="mt-6 text-sm text-[#242672] opacity-80">
        © {year ?? ""} DinoBot. Pour les enfants curieux !
      </footer>
    </main>
  );
}
