import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RAG Workspace — AI Document Intelligence",
  description: "Production-grade multi-turn RAG search engine with semantic caching, adaptive retrieval, and self-evaluation.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="antialiased" style={{ background: "var(--background)", color: "var(--foreground)" }}>
        {children}
      </body>
    </html>
  );
}
