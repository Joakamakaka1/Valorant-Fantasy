"use client";

import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useAuth } from "@/lib/context/auth-context";
import { UserPlus, Mail, Lock, User, Loader2, AlertCircle } from "lucide-react";
import Link from "next/link";
import { FormField } from "@/components/ui/form-field";

// Zod Schema Definition with robust validation
const registerSchema = z.object({
  email: z.string().email("Formato de email inválido"),
  username: z
    .string()
    .min(3, "El nombre de usuario debe tener al menos 3 caracteres")
    .max(20, "El nombre de usuario no puede exceder 20 caracteres")
    .regex(
      /^[a-zA-Z0-9_]+$/,
      "Solo se permiten letras, números y guiones bajos",
    ),
  password: z
    .string()
    .min(8, "La contraseña debe tener al menos 8 caracteres")
    .regex(/[A-Z]/, "Debe contener al menos una letra mayúscula")
    .regex(/[a-z]/, "Debe contener al menos una letra minúscula")
    .regex(/[0-9]/, "Debe contener al menos un número"),
});

type RegisterFormValues = z.infer<typeof registerSchema>;

export default function RegisterForm() {
  const { register: registerUser } = useAuth();

  // React Hook Form Setup
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: "",
      username: "",
      password: "",
    },
  });

  // Submit Handler
  const onSubmit = async (data: RegisterFormValues) => {
    try {
      await registerUser(data);
    } catch (err: any) {
      // Set root error or specific field error
      setError("root", {
        type: "server",
        message: err.message || "Error al crear el perfil",
      });
    }
  };

  return (
    <div className="w-full max-w-md p-8 bg-zinc-900/60 backdrop-blur-xl border border-zinc-800 rounded-2xl shadow-2xl animate-in fade-in zoom-in duration-300">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-black text-white tracking-tighter uppercase mb-2">
          Nuevo <span className="text-[#ff4655]">Recluta</span>
        </h1>
        <p className="text-zinc-400 text-sm italic font-medium">
          Crea tu identidad y únete a la competición.
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {/* Username Field */}
        <FormField
          label="Alias de Jugador"
          error={errors.username?.message}
          icon={User}
        >
          <input
            {...register("username")}
            type="text"
            placeholder="vct_pro_player"
            className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
          />
        </FormField>

        {/* Email Field */}
        <FormField
          label="Email Operativo"
          error={errors.email?.message}
          icon={Mail}
        >
          <input
            {...register("email")}
            type="email"
            placeholder="tu-email@gmail.com"
            className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
          />
        </FormField>

        {/* Password Field */}
        <FormField
          label="Clave Segmentada"
          error={errors.password?.message}
          icon={Lock}
        >
          <input
            {...register("password")}
            type="password"
            placeholder="Mínimo 8 caracteres"
            className="w-full bg-zinc-800/50 border border-zinc-700/50 rounded-xl py-3 pl-11 pr-4 text-white placeholder:text-zinc-600 focus:outline-none focus:border-[#ff4655]/50 focus:ring-1 focus:ring-[#ff4655]/30 transition-all"
          />
        </FormField>

        {/* Root Error (Server Error) */}
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
              Confirmar Reclutamiento
              <UserPlus className="w-4 h-4" />
            </>
          )}
        </button>
      </form>

      <div className="flex flex-col items-center gap-4 mt-8 pt-6 border-t border-zinc-800/50">
        <p className="text-zinc-500 text-sm">
          ¿Ya eres veterano?{" "}
          <Link
            href="/login"
            className="text-[#ff4655] font-bold hover:underline"
          >
            Entra aquí
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
