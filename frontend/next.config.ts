import type { NextConfig } from "next";

// El navegador se comunica exclusivamente con Next.js -- Next.js es el único consumidor HTTP
// del backend (spec 009, principio arquitectónico). Este rewrite es el único lugar donde el
// frontend "conoce" la URL real de FastAPI; ningún componente cliente debería referenciarla.
const nextConfig: NextConfig = {
  async rewrites() {
    const backendUrl = process.env.BACKEND_URL;
    if (!backendUrl) {
      throw new Error("BACKEND_URL no está configurado (ver frontend/.env.local)");
    }
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
