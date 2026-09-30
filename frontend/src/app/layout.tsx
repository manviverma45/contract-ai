import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Contract AI",
  description: "AI-powered contract analysis",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}