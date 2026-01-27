import LoginForm from "@/components/auth/login-form";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Login | Valorant Fantasy",
  description: "Entra a tu cuenta de Valorant Fantasy y gestiona tu equipo.",
};

export default function LoginPage() {
  return <LoginForm />;
}
