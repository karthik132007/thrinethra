import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {
  title: "Trinethra — Command Centre",
  description:
    "Evidence-grounded public safety situational intelligence. Human judgment, informed.",
};
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
