import type { Metadata } from 'next';
import './globals.css';
import { AuthProvider } from '@/contexts/AuthContext';

export const metadata: Metadata = {
  title: 'Adamani AI RAG - Invoice & PDF Processing',
  description: 'AI-powered invoice and PDF document processing with RAG',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
