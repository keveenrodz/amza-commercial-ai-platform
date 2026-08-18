import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Amza Commercial AI Platform",
  description: "Advisor Workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es" suppressHydrationWarning>
      <head>
        {/* Antes de que React hidrate: lee el tema elegido y lo aplica de inmediato, para
            evitar el parpadeo de tema incorrecto al cargar (spec 011). suppressHydrationWarning
            en <html> es necesario porque este script cambia data-theme antes de la hidratación,
            así que el marcado del servidor y el del cliente difieren en ese atributo a propósito. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                var t = localStorage.getItem('amza-theme');
                if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
