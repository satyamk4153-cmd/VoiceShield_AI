import type { Metadata } from "next";
import "./globals.css";
import { AppLayout } from "../components/AppLayout";

export const metadata: Metadata = {
  title: "VoiceShield AI — Protect every voice",
  description: "Enterprise voice authentication and telephony fraud prevention. Multi-modal voice anti-spoofing, speaker verification, and conversational intent analysis.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className="bg-[#F8FAFC] text-slate-900 antialiased selection:bg-blue-100 selection:text-blue-900">
        <AppLayout>{children}</AppLayout>
      </body>
    </html>
  );
}
