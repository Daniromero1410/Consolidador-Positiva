'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { API_BASE } from '@/config/api';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'admin' | 'analyst' | 'projects';
}

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (username: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  refreshAccessToken: () => Promise<boolean>;
}

// ══════════════════════════════════════════════════════════════
// CONTEXT
// ══════════════════════════════════════════════════════════════

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth debe usarse dentro de AuthProvider');
  return ctx;
};

// ══════════════════════════════════════════════════════════════
// HELPER: localStorage seguro
// ══════════════════════════════════════════════════════════════

const storage = {
  get: (key: string): string | null => {
    if (typeof window === 'undefined') return null;
    try { return localStorage.getItem(key); } catch { return null; }
  },
  set: (key: string, value: string) => {
    if (typeof window === 'undefined') return;
    try { localStorage.setItem(key, value); } catch {}
  },
  remove: (key: string) => {
    if (typeof window === 'undefined') return;
    try { localStorage.removeItem(key); } catch {}
  },
};

// ══════════════════════════════════════════════════════════════
// RUTAS PÚBLICAS (no requieren autenticación)
// ══════════════════════════════════════════════════════════════

const PUBLIC_ROUTES = ['/login', '/certificados'];

export function isPublicRoute(pathname: string): boolean {
  return PUBLIC_ROUTES.some(route => pathname.startsWith(route));
}

// ══════════════════════════════════════════════════════════════
// PROVIDER
// ══════════════════════════════════════════════════════════════

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();

  const [state, setState] = useState<AuthState>({
    user: null,
    accessToken: null,
    refreshToken: null,
    isAuthenticated: false,
    isLoading: true,
  });

  // Cargar sesión al iniciar
  useEffect(() => {
    const accessToken = storage.get('access_token');
    const refreshToken = storage.get('refresh_token');
    const userStr = storage.get('user');

    if (accessToken && userStr) {
      try {
        const user = JSON.parse(userStr);
        setState({
          user,
          accessToken,
          refreshToken,
          isAuthenticated: true,
          isLoading: false,
        });
      } catch {
        clearSession();
        setState(prev => ({ ...prev, isLoading: false }));
      }
    } else {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  }, []);

  // Proteger rutas
  useEffect(() => {
    if (state.isLoading) return;

    if (!state.isAuthenticated && !isPublicRoute(pathname)) {
      router.push('/login');
    }

    if (state.isAuthenticated && pathname === '/login') {
      router.push('/');
    }
  }, [state.isAuthenticated, state.isLoading, pathname, router]);

  function clearSession() {
    storage.remove('access_token');
    storage.remove('refresh_token');
    storage.remove('user');
    setState({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
    });
  }

  // ── LOGIN ──
  async function login(username: string, password: string) {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        return { success: false, error: data.detail || 'Error de autenticación' };
      }

      // Guardar sesión
      storage.set('access_token', data.access_token);
      storage.set('refresh_token', data.refresh_token);
      storage.set('user', JSON.stringify(data.user));

      setState({
        user: data.user,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        isAuthenticated: true,
        isLoading: false,
      });

      return { success: true };
    } catch (err: any) {
      return { success: false, error: 'Error de conexión con el servidor' };
    }
  }

  // ── LOGOUT ──
  function logout() {
    clearSession();
    router.push('/login');
  }

  // ── REFRESH TOKEN ──
  async function refreshAccessToken(): Promise<boolean> {
    const refreshToken = storage.get('refresh_token');
    if (!refreshToken) return false;

    try {
      const res = await fetch(`${API_BASE}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (!res.ok) {
        clearSession();
        return false;
      }

      const data = await res.json();
      storage.set('access_token', data.access_token);
      storage.set('refresh_token', data.refresh_token);

      setState(prev => ({
        ...prev,
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
      }));

      return true;
    } catch {
      clearSession();
      return false;
    }
  }

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshAccessToken }}>
      {children}
    </AuthContext.Provider>
  );
}
