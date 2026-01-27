import RegisterForm from "@/components/auth/register-form";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Registro | Valorant Fantasy",
  description: "Crea tu cuenta de Valorant Fantasy para empezar a competir.",
};

export default function RegisterPage() {
  return <RegisterForm />;
}
