import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AbiaCS Assistant — Abia State Civil Service AI Chatbot",
  description:
    "Get instant, accurate answers about Abia State Civil Service rules, regulations, procedures, and policies.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 antialiased">{children}</body>
    </html>
  );
}
