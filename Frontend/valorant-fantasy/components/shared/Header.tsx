import Link from "next/link";
import { AnimatedThemeToggler } from "../ui/animated-theme-toggler";

export default function Header() {
  return (
    <nav className="w-full flex justify-between px-12 py-4 text-white">
      <ul>
        <img src="/Icono.webp" alt="Icono" className="w-18" />
      </ul>
      <ul className="flex items-center gap-12">
        <li className="text-xl">Yo</li>
        <li className="text-xl">Proyectos</li>
        <li className="text-xl">Contáctame</li>
        <li className="text-xl">Ligas</li>
      </ul>
      <ul className="flex items-center gap-4">
        <li className="text-xl">18:31</li>
        <AnimatedThemeToggler />
      </ul>
    </nav>
  );
}
