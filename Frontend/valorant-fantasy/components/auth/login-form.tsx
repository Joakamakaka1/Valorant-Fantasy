"use client";

import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuth } from "@/lib/context/auth-context";
import { LogIn, Mail, Lock, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";

// 1. Zod Schema Definition
const loginSchema = z.object({
  email: z.string().email("Formato de email inválido"),
  password: z.string().min(1, "La contraseña es requerida"),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export default function LoginForm() {
  const { login } = useAuth();

  // 2. React Hook Form Setup
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  // 3. Submit Handler
  const onSubmit = async (data: LoginFormValues) => {
    try {
      await login(data);
    } catch (err: any) {
      // Set root error or specific field error
      setError("root", {
        type: "server",
        message: err.message || "Credenciales incorrectas",
      });
    }
  };

  return (
    <div className="w-full max-w-md p-8 bg-zinc-900/60 backdrop-blur-xl border border-zinc-800 rounded-2xl shadow-2xl animate-in fade-in zoom-in duration-300">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-black text-white tracking-tighter uppercase mb-2">
          Hacer <span className="text-[#ff4655]">Login</span>
        </h1>
        <p className="text-zinc-400 text-sm italic font-medium">
          Entra al servidor y domina el bracket.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Email Field */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest pl-1">
            Email Operativo
          </label>
          <div className="relative group">
            <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-[#ff4655] transition-colors" />
            <input
              {...register("email")}
              type="email"
              placeholder="tu-alias@vlr.gg"
              className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
            />
          </div>
          {errors.email && (
            <p className="text-red-500 text-xs pl-1 font-medium flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.email.message}
            </p>
          )}
        </div>

        {/* Password Field */}
        <div className="space-y-2">
          <label className="text-xs font-bold text-zinc-500 uppercase tracking-widest pl-1">
            Clave de Acceso
          </label>
          <div className="relative group">
            <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-[#ff4655] transition-colors" />
            <input
              {...register("password")}
              type="password"
              placeholder="••••••••"
              className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
            />
          </div>
          {errors.password && (
            <p className="text-red-500 text-xs pl-1 font-medium flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              {errors.password.message}
            </p>
          )}
        </div>

        {/* Root Error (Auth Failed) */}
        {errors.root && (
          <div className="bg-red-500/10 border border-red-500/20 text-red-500 text-xs py-2 px-3 rounded-lg font-medium flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            {errors.root.message}
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-[#ff4655] hover:bg-[#ff4655]/90 text-white font-black py-4 rounded-xl shadow-[0_0_20px_rgba(255,70,85,0.3)] transition-all active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 uppercase tracking-widest"
        >
          {isSubmitting ? (
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
