import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Autonomous Agent Visual Engineering Console (Track 1)",
  description:
    "Next.js 5-Stage Visual Engineering Console (BUILD, RUN, UNDERSTAND, IMPROVE, VALIDATE) and 4-Axis Scorecard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 antialiased selection:bg-cyan-500/20 selection:text-cyan-200">
        {children}
      </body>
    </html>
  );
}
