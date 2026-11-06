import type { Metadata } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "DRIFTGUARD 2.0 — Financial Fraud Intelligence Platform",
  description: "Adaptive Streaming Fraud & Threat Detection System with 7 Specialist Experts and Real-Time WebSockets",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-canvas min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

