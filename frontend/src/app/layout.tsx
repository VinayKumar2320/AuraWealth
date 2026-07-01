import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AuraWealth | Dynamic Micro-Investing Allocator",
  description: "Get daily, research-backed, live US stock recommendations optimized for fractional share micro-investing.",
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
