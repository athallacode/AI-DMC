'use client';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Upload, ClipboardCheck, Archive, LogOut } from 'lucide-react';
import { api, Document, logout, token, User } from '@/lib/api';
import { ConfidenceThreshold, ErrorMessage } from './ui';
const links = [{ href: '/unggah', name: 'Unggah', icon: Upload }, { href: '/verifikasi', name: 'Verifikasi', icon: ClipboardCheck }, { href: '/arsip', name: 'Arsip', icon: Archive }];
export function Brand({ demo = false }: { demo?: boolean }) { return <div className="brand"><span className="brand-university">Telkom<span>University</span></span><span className="brand-coe">CoE<span>AIIS</span></span><span className="brand-divider" /><span>AI-DMC</span>{demo && <span className="demo-pill" aria-label="Demo: hasil simulasi, bukan AI asli">Demo</span>}</div>; }
export default function Shell({ children, refreshKey = 0 }: { children: React.ReactNode; refreshKey?: number }) {
  const path = usePathname(); const router = useRouter(); const [user, setUser] = useState<User | null>(null); const [count, setCount] = useState(0); const [mode, setMode] = useState(''); const [threshold, setThreshold] = useState(.85); const [error, setError] = useState('');
  useEffect(() => { if (!token()) { router.replace('/login'); return; } api<User>('/auth/me').then(setUser).catch(e => setError(e.message)); api<{pipeline_mode: string; confidence_threshold?: number}>('/health').then(data => {setMode(data.pipeline_mode); if (typeof data.confidence_threshold === 'number') setThreshold(data.confidence_threshold);}).catch(() => {}); }, [router]);
  useEffect(() => { if (token()) api<Document[]>('/documents?status=menunggu_verifikasi').then(docs => setCount(docs.length)).catch(() => {}); }, [path, refreshKey]);
  const nav = <>{links.map(link => <Link key={link.href} href={link.href} aria-current={path === link.href ? 'page' : undefined}><link.icon size={16} strokeWidth={1.75} /><span>{link.name}</span>{link.href === '/verifikasi' && count > 0 && <span className="nav-count">{count}</span>}</Link>)}</>;
  return <><a className="skip-link" href="#main">Lewati ke konten</a><header className="navbar glass"><div className="nav-inner"><Brand demo={mode === 'mock'} /><nav aria-label="Navigasi utama" className="desktop-nav segmented">{nav}</nav><details className="account" onKeyDown={event => { if (event.key === 'Escape') { event.currentTarget.open = false; event.currentTarget.querySelector('summary')?.focus(); } }}><summary className="avatar" aria-label="Menu akun">{user?.nama.slice(0, 1) || 'D'}</summary><div className="account-dropdown"><p>{user?.nama}</p><button className="text-button" onClick={logout}><LogOut size={16} />Keluar</button></div></details></div></header><main id="main" className="main"><ErrorMessage message={error} />{user ? <ConfidenceThreshold.Provider value={threshold}>{children}</ConfidenceThreshold.Provider> : <p className="muted">Memeriksa sesi…</p>}</main><nav aria-label="Navigasi HP" className="mobile-nav glass">{nav}</nav></>;
}
