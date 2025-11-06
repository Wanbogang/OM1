// frontend/src/app/layout.tsx

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Link from 'next/link'; // Impor Link dari Next.js

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'SmartFarm Dashboard',
  description: 'Advanced analytics and swarm intelligence for smart farming',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-100">
          {/* Header dengan Navigasi */}
          <header className="bg-gray-800 text-white p-4 shadow-md">
            <div className="container mx-auto flex justify-between items-center">
              <h1 className="text-xl font-bold">🌾 SmartFarm System</h1>
              <nav>
                <ul className="flex space-x-6">
                  <li><Link href="/" className="hover:underline">Home</Link></li>
                  <li><Link href="/dashboard" className="hover:underline">Analytics</Link></li>
                  <li><Link href="/predict" className="hover:underline">Predict</Link></li>
                  {/* Link baru untuk Swarm Dashboard */}
                  <li><Link href="/swarm" className="hover:underline">Swarm</Link></li>
                </ul>
              </nav>
            </div>
          </header>

          {/* Main Content */}
          <main className="container mx-auto p-4">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
