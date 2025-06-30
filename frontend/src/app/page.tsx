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
        "👋 Bonjour ! Je suis Facty. Pour commencer, dis-moi ton prénom 🙂",
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
    let payload: any = {};
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
    <main className="min-h-screen bg-gradient-to-br from-pink-100 via-yellow-100 to-blue-100 flex flex-col items-center py-6 px-2">
      <div className="w-full max-w-md bg-white/80 rounded-3xl shadow-xl p-6 flex flex-col items-center">
        <Image
          src="/assets/logo.jpeg"
          alt="Facty Logo"
          width={120}
          height={120}
          className="rounded-2xl mb-2 border-4 border-pink-300 shadow-lg"
        />
        <h1 className="text-3xl font-extrabold text-pink-600 mb-1 text-center drop-shadow-lg">
          Facty
        </h1>
        <p className="text-lg text-yellow-700 font-semibold mb-4 text-center">
          🤖 Le fact-checker rigolo pour enfants !<br />Vérifie si une info est vraie ou fausse, en toute simplicité.
        </p>
        <div className="w-full flex flex-col gap-2 bg-blue-50 rounded-xl p-3 h-96 overflow-y-auto mb-3 border-2 border-blue-200">
          {messages.map((msg, idx) => (
            <div
              key={idx}
              className={`flex items-start gap-2 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
            >
              {msg.role === "assistant" && (
                <Image
                  src="/assets/bot_avatar.jpeg"
                  alt="Bot"
                  width={40}
                  height={40}
                  className="rounded-full border-2 border-pink-300"
                />
              )}
              <div
                className={`px-4 py-2 rounded-2xl max-w-[70%] text-base font-medium shadow-md ${
                  msg.role === "user"
                    ? "bg-pink-200 text-pink-900 self-end"
                    : "bg-yellow-100 text-blue-900"
                }`}
              >
                {msg.content}
              </div>
              {msg.role === "user" && (
                <Image
                  src="/assets/user_avatar.jpeg"
                  alt="User"
                  width={40}
                  height={40}
                  className="rounded-full border-2 border-yellow-400"
                />
              )}
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>
        <div className="w-full flex gap-2 mt-2">
          <input
            type="text"
            className="flex-1 rounded-xl border-2 border-pink-300 px-4 py-2 text-lg focus:outline-none focus:ring-2 focus:ring-pink-400 bg-white text-pink-900 placeholder:text-pink-400"
            placeholder={
              step === "awaiting_name"
                ? "Ton prénom..."
                : step === "awaiting_age"
                ? "Ton âge..."
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
            className="bg-pink-400 hover:bg-pink-500 text-white font-bold px-5 py-2 rounded-xl shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
            aria-label="Envoyer"
          >
            {loading ? "..." : "Envoyer"}
          </button>
        </div>
      </div>
      <footer className="mt-6 text-sm text-blue-500 opacity-80">
        © {year ?? ""} Facty. Pour les enfants curieux !
      </footer>
    </main>
  );
}
