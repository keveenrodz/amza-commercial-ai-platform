import type { Metadata } from "next";
import { Manrope } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

// Mismo rango de peso que el mockup (500-800) -- ver spec 013b, sección 2, sobre por qué el
// texto sin peso explícito (cuerpo de mensajes/notas) deliberadamente NO usa esta fuente.
const manrope = Manrope({
  variable: "--font-manrope",
  weight: ["500", "600", "700", "800"],
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
      <body className={`${manrope.variable} antialiased`}>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
