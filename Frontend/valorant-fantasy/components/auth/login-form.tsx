"use client";

import React, { useState } from "react";
import { useAuth } from "@/lib/context/auth-context";
import { LogIn, Mail, Lock, Loader2 } from "lucide-react";
import Link from "next/link";

export default function LoginForm() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      await login({ email, password });
    } catch (err: any) {
      setError(err.response?.data?.message || "Credenciales incorrectas");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md p-8 bg-zinc-900/60 backdrop-blur-xl border border-zinc-800 rounded-2xl shadow-2xl">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-black text-white tracking-tighter uppercase mb-2">
          Hacer <span className="text-[#ff4655]">Login</span>
        </h1>
        <p className="text-zinc-400 text-sm italic font-medium">
          Entra al servidor y domina el bracket.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div className="space-y-2">
          <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest pl-1">
            Email Operativo
          </label>
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-[#ff4655] transition-colors" />
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tu-alias@vlr.gg"
              className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest pl-1">
            Clave de Acceso
          </label>
          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-[#ff4655] transition-colors" />
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
              required
            />
          </div>
        </div>

        {error && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-xs py-2 px-3 rounded-lg font-medium">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isLoading}
          className="w-full bg-[#ff4655] hover:bg-[#ff4655]/90 text-white font-black py-4 rounded-xl shadow-[0_0_20px_rgba(255,70,85,0.3)] transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 uppercase tracking-widest"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : (
            <>
              Establecer Conexión
              <LogIn className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="flex flex-col items-center gap-4 mt-8 pt-6 border-t border-zinc-800/50">
        <p className="text-zinc-500 text-sm">
          ¿Aún no tienes equipo?{" "}
          <Link
            href="/register"
            className="text-[#ff4655] font-bold hover:underline"
          >
            Reclútate aquí
          </Link>
        </p>
        <Link
          href="/"
          className="text-xs text-zinc-600 hover:text-zinc-400 uppercase tracking-tighter italic"
        >
          Volver a la base
        </Link>
      </div>
    </div>
  );
}
