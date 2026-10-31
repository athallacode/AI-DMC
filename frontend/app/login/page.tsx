'use client';
import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { api, User } from '@/lib/api';
import { Brand } from '@/components/shell';
import { ErrorMessage } from '@/components/ui';
export default function Login() {
  const router = useRouter(); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  async function submit(event: FormEvent<HTMLFormElement>) { event.preventDefault(); setError(''); setBusy(true); const data = new FormData(event.currentTarget); try { const result = await api<{access_token: string; user: User}>('/auth/login', { method: 'POST', body: JSON.stringify({username: data.get('username'), password: data.get('password')}) }); sessionStorage.setItem('ai-dmc-token', result.access_token); router.replace('/unggah'); } catch (e) { setError(e instanceof Error ? e.message : 'Login belum berhasil. Coba lagi.'); } finally { setBusy(false); } }
  return <main className="login-page"><section className="login-card card"><Brand /><h1>Masuk</h1><p className="muted">Kelola dokumen Anda di CoE AIIS.</p><form onSubmit={submit}><label>Username<input name="username" autoComplete="username" required autoFocus /></label><label>Password<input name="password" type="password" autoComplete="current-password" required /></label><ErrorMessage message={error} /><button className="primary full" disabled={busy}>{busy ? 'Memeriksa…' : 'Masuk'}</button></form><p className="login-footnote">Gunakan akun yang diberikan pengelola.</p></section></main>;
}
