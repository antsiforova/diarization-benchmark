import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Diarization Benchmark Dashboard",
  description: "Continuous benchmark results for speaker diarization models",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased min-h-screen bg-background">
        <div className="container mx-auto py-8">
          <header className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Diarization Benchmark</h1>
            <p className="text-muted-foreground">Continuous evaluation dashboard for speaker diarization models</p>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
