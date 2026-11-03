import type { Metadata } from 'next';
import { ClerkProvider } from '@clerk/nextjs';
import './globals.css';
import Navbar from '@/components/Navbar';
import Footer from '@/components/Footer';

export const metadata: Metadata = {
  title: 'PolicyGPT - Find government schemes you qualify for',
  description: 'Discover, match, and navigate government welfare schemes, startup grants, and scholarships with AI.',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Figtree:ital,wght@0,400;0,500;0,600;0,700;0,800;1,400&family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700;12..96,800&family=Noto+Sans+Devanagari:wght@400;700&family=Noto+Sans+Kannada:wght@400;700&display=swap" rel="stylesheet" />
      </head>
      <body className="h-full flex flex-col bg-paper text-ink antialiased min-h-screen">
        <ClerkProvider>
          <Navbar />
          <main className="flex-1 flex flex-col container mx-auto px-4 py-8 max-w-7xl">
            {children}
          </main>
          <Footer />
        </ClerkProvider>
      </body>
    </html>
  );
}
