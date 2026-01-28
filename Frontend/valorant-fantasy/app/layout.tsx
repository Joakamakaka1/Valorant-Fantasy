import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Providers from "@/components/providers";
import { Toaster } from "sonner";
import { getSession } from "@/lib/actions/auth-actions";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Fantasy Valorant - Competitive Esports Fantasy League",
    template: "%s | Fantasy Valorant",
  },
  description:
    "Build your dream Valorant esports team and compete in fantasy leagues with real VCT statistics.",
  keywords: ["valorant", "fantasy", "esports", "vct", "competitive"],
};

/**
 * Root Layout - Server Component
 *
 * Fetches user session on the server and passes it to client providers.
 * This eliminates the waterfall request pattern and improves initial load performance.
 */
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // Fetch user session server-side
  const user = await getSession();

  return (
    <html lang="en" className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers initialUser={user}>
          {children}
          <Toaster richColors position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
