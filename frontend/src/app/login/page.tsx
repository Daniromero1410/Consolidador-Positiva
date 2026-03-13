'use client';

import { useState, FormEvent } from 'react';
import { useAuth } from '@/lib/auth';
import { Shield, Eye, EyeOff, Lock, User, AlertTriangle, Loader2, FileSpreadsheet } from 'lucide-react';

export default function LoginPage() {
    const { login, isLoading: authLoading } = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    // Tema
    const [theme] = useState<'dark' | 'light'>(() => {
        if (typeof window !== 'undefined') {
            return (localStorage.getItem('theme') as 'dark' | 'light') || 'dark';
        }
        return 'dark';
    });
    const isDark = theme === 'dark';

    const handleSubmit = async (e: FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const result = await login(username, password);

        if (!result.success) {
            setError(result.error || 'Error de autenticación');
        }

        setLoading(false);
    };

    if (authLoading) {
        return (
            <div
                className="min-h-screen flex items-center justify-center"
                style={{ backgroundColor: isDark ? '#030712' : '#f9fafb' }}
            >
                <Loader2 className="w-8 h-8 animate-spin" style={{ color: '#f97316' }} />
            </div>
        );
    }

    return (
        <div
            className="min-h-screen flex items-center justify-center px-4"
            style={{
                backgroundColor: isDark ? '#030712' : '#f0f2f5',
                backgroundImage: isDark
                    ? 'radial-gradient(ellipse at top, rgba(249,115,22,0.08) 0%, transparent 60%)'
                    : 'radial-gradient(ellipse at top, rgba(249,115,22,0.05) 0%, transparent 60%)'
            }}
        >
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div
                        className="w-16 h-16 rounded-2xl flex items-center justify-center mx-auto mb-4"
                        style={{ background: 'linear-gradient(135deg, #f97316, #ea580c)' }}
                    >
                        <FileSpreadsheet className="w-8 h-8 text-white" />
                    </div>
                    <h1
                        className="text-2xl font-bold"
                        style={{ color: isDark ? '#ffffff' : '#111827' }}
                    >
                        Gestar Innovación
                    </h1>
                    <p style={{ color: isDark ? '#6b7280' : '#9ca3af' }} className="text-sm mt-1">
                        Plataforma de Gestión POSITIVA
                    </p>
                </div>

                {/* Card de login */}
                <div
                    className="rounded-2xl p-8 shadow-xl"
                    style={{
                        backgroundColor: isDark ? '#111827' : '#ffffff',
                        border: `1px solid ${isDark ? '#1f2937' : '#e5e7eb'}`,
                        boxShadow: isDark
                            ? '0 25px 50px rgba(0,0,0,0.5)'
                            : '0 25px 50px rgba(0,0,0,0.08)'
                    }}
                >
                    <div className="flex items-center gap-2 mb-6">
                        <Shield className="w-5 h-5" style={{ color: '#f97316' }} />
                        <h2
                            className="text-lg font-semibold"
                            style={{ color: isDark ? '#ffffff' : '#111827' }}
                        >
                            Iniciar Sesión
                        </h2>
                    </div>

                    {/* Error */}
                    {error && (
                        <div
                            className="flex items-center gap-2 p-3 rounded-xl mb-4 text-sm"
                            style={{
                                backgroundColor: isDark ? 'rgba(239,68,68,0.1)' : '#fef2f2',
                                color: '#ef4444',
                                border: `1px solid ${isDark ? 'rgba(239,68,68,0.2)' : '#fecaca'}`
                            }}
                        >
                            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Username */}
                        <div>
                            <label
                                className="block text-sm font-medium mb-1.5"
                                style={{ color: isDark ? '#d1d5db' : '#374151' }}
                            >
                                Usuario
                            </label>
                            <div className="relative">
                                <User
                                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
                                    style={{ color: isDark ? '#6b7280' : '#9ca3af' }}
                                />
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="Ingrese su usuario"
                                    required
                                    autoComplete="username"
                                    className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm transition-all duration-200 outline-none"
                                    style={{
                                        backgroundColor: isDark ? '#1f2937' : '#f9fafb',
                                        color: isDark ? '#ffffff' : '#111827',
                                        border: `1px solid ${isDark ? '#374151' : '#d1d5db'}`,
                                    }}
                                    onFocus={(e) => e.target.style.borderColor = '#f97316'}
                                    onBlur={(e) => e.target.style.borderColor = isDark ? '#374151' : '#d1d5db'}
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div>
                            <label
                                className="block text-sm font-medium mb-1.5"
                                style={{ color: isDark ? '#d1d5db' : '#374151' }}
                            >
                                Contraseña
                            </label>
                            <div className="relative">
                                <Lock
                                    className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4"
                                    style={{ color: isDark ? '#6b7280' : '#9ca3af' }}
                                />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Ingrese su contraseña"
                                    required
                                    autoComplete="current-password"
                                    className="w-full pl-10 pr-10 py-2.5 rounded-xl text-sm transition-all duration-200 outline-none"
                                    style={{
                                        backgroundColor: isDark ? '#1f2937' : '#f9fafb',
                                        color: isDark ? '#ffffff' : '#111827',
                                        border: `1px solid ${isDark ? '#374151' : '#d1d5db'}`,
                                    }}
                                    onFocus={(e) => e.target.style.borderColor = '#f97316'}
                                    onBlur={(e) => e.target.style.borderColor = isDark ? '#374151' : '#d1d5db'}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2"
                                    style={{ color: isDark ? '#6b7280' : '#9ca3af' }}
                                >
                                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                </button>
                            </div>
                        </div>

                        {/* Submit */}
                        <button
                            type="submit"
                            disabled={loading || !username || !password}
                            className="w-full py-2.5 rounded-xl text-white font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2"
                            style={{
                                background: loading ? '#9ca3af' : 'linear-gradient(135deg, #f97316, #ea580c)',
                                opacity: (!username || !password) ? 0.6 : 1,
                                cursor: loading ? 'not-allowed' : 'pointer',
                            }}
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                    Autenticando...
                                </>
                            ) : (
                                <>
                                    <Lock className="w-4 h-4" />
                                    Ingresar
                                </>
                            )}
                        </button>
                    </form>

                    {/* Security info */}
                    <div
                        className="mt-6 pt-4 text-center"
                        style={{ borderTop: `1px solid ${isDark ? '#1f2937' : '#e5e7eb'}` }}
                    >
                        <div className="flex items-center justify-center gap-1.5 text-xs" style={{ color: isDark ? '#4b5563' : '#9ca3af' }}>
                            <Shield className="w-3 h-3" />
                            <span>Conexión protegida con JWT + bcrypt</span>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center mt-6 text-xs" style={{ color: isDark ? '#4b5563' : '#9ca3af' }}>
                    © 2024 - 2025 Gestar Innovación S.A.S · Red Asistencial
                </p>
            </div>
        </div>
    );
}
