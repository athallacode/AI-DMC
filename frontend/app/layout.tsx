import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
const inter = Inter({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-inter',
});
export const metadata: Metadata = { title: 'AI-DMC | CoE AIIS', description: 'Pengelolaan dan verifikasi dokumen dosen CoE AIIS.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="id" className={`${inter.className} ${inter.variable}`}><body>{children}</body></html>;
}
