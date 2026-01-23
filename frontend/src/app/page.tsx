'use client';

import { useEffect, useState } from 'react';
import {
  FileSpreadsheet,
  Server,
  Play,
  Download,
  CheckCircle,
  XCircle,
  AlertCircle,
  ArrowRight,
  HardDrive,
  Calendar,
  Zap
} from 'lucide-react';
import Link from 'next/link';
import { API_BASE } from '@/config/api';

// Hook para obtener el tema
function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  
  useEffect(() => {
    const checkTheme = () => {
      const saved = localStorage.getItem('theme');
      setTheme(saved === 'dark' ? 'dark' : 'light');
    };
    
    checkTheme();
    window.addEventListener('storage', checkTheme);
    const interval = setInterval(checkTheme, 100);
    
    return () => {
      window.removeEventListener('storage', checkTheme);
      clearInterval(interval);
    };
  }, []);
  
  return theme;
}

export default function HomePage() {
  const theme = useTheme();
  const isDark = theme === 'dark';
  
  const [maestraCargada, setMaestraCargada] = useState<boolean | null>(null);
  const [maestraArchivo, setMaestraArchivo] = useState<string>('');
  const [maestraContratos, setMaestraContratos] = useState(0);
  const [años, setAños] = useState<number[]>([]);
  const [sftpConectado, setSftpConectado] = useState(false);
  const [loading, setLoading] = useState(true);

  // Estilos basados en tema
  const styles = {
    card: {
      backgroundColor: isDark ? '#1f2937' : '#ffffff',
      borderColor: isDark ? '#374151' : '#e5e7eb',
    },
    text: {
      primary: isDark ? '#ffffff' : '#111827',
      secondary: isDark ? '#9ca3af' : '#6b7280',
      muted: isDark ? '#6b7280' : '#9ca3af',
    },
  };

  useEffect(() => {
    const cargar = async () => {
      try {
        const [maestraRes, sftpRes] = await Promise.all([
          fetch(`${API_BASE}/maestra/estado`).catch(() => null),
          fetch(`${API_BASE}/sftp/estado`).catch(() => null)
        ]);
        
        if (maestraRes?.ok) {
          const data = await maestraRes.json();
          setMaestraCargada(data.cargada);
          setMaestraArchivo(data.archivo || '');
          setMaestraContratos(data.total_contratos || 0);
          setAños(data.años_disponibles || []);
        } else {
          setMaestraCargada(false);
        }
        
        if (sftpRes?.ok) {
          const data = await sftpRes.json();
          setSftpConectado(data.conectado);
        }
      } catch (err) {
        console.error('Error:', err);
        setMaestraCargada(false);
      } finally {
        setLoading(false);
      }
    };
    
    cargar();
  }, []);

  const pasos = [
    {
      numero: 1,
      titulo: 'Cargar Maestra',
      descripcion: 'Sube el archivo Excel con los contratos',
      href: '/maestra',
      icon: FileSpreadsheet,
      completado: maestraCargada || false,
      info: maestraCargada ? `${maestraContratos.toLocaleString()} contratos` : 'Sin cargar'
    },
    {
      numero: 2,
      titulo: 'Verificar SFTP',
      descripcion: 'Conectar al servidor GoAnywhere',
      href: '/sftp',
      icon: Server,
      completado: sftpConectado,
      info: sftpConectado ? 'Conectado' : 'Sin conexión'
    },
    {
      numero: 3,
      titulo: 'Procesar',
      descripcion: 'Ejecutar el consolidador T25',
      href: '/procesar',
      icon: Play,
      completado: false,
      info: 'Listo para procesar'
    },
    {
      numero: 4,
      titulo: 'Descargar',
      descripcion: 'Obtener archivos generados',
      href: '/descargas',
      icon: Download,
      completado: false,
      info: 'Ver descargas'
    }
  ];

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 rounded w-1/3 mb-4" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }} />
          <div className="h-4 rounded w-1/2 mb-8" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }} />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {[1,2,3,4].map(i => (
              <div key={i} className="h-40 rounded-2xl" style={{ backgroundColor: isDark ? '#374151' : '#e5e7eb' }} />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: styles.text.primary }}>
          Dashboard
        </h1>
        <p style={{ color: styles.text.secondary }} className="mt-1">
          Sistema de consolidación de tarifas T25 - POSITIVA
        </p>
      </div>

      {/* Banner de maestra activa */}
      {maestraCargada && (
        <div 
          className="rounded-2xl p-6 text-white"
          style={{ background: 'linear-gradient(135deg, #f97316, #ea580c)' }}
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <div 
                className="w-12 h-12 rounded-xl flex items-center justify-center"
                style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
              >
                <HardDrive className="w-6 h-6" />
              </div>
              <div>
                <p className="text-sm font-medium" style={{ color: 'rgba(255,255,255,0.8)' }}>
                  Maestra Activa
                </p>
                <h2 className="text-lg font-bold">{maestraArchivo}</h2>
              </div>
            </div>
            
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold">{maestraContratos.toLocaleString()}</p>
                <p className="text-xs" style={{ color: 'rgba(255,255,255,0.7)' }}>Contratos</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{años.length}</p>
                <p className="text-xs" style={{ color: 'rgba(255,255,255,0.7)' }}>Años</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tarjetas de pasos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {pasos.map((paso) => {
          const Icon = paso.icon;
          
          return (
            <Link 
              key={paso.numero}
              href={paso.href}
              className="group rounded-2xl p-5 transition-all duration-200"
              style={{ 
                ...styles.card, 
                border: `1px solid ${styles.card.borderColor}`,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = isDark 
                  ? '0 10px 40px rgba(0,0,0,0.3)' 
                  : '0 10px 40px rgba(0,0,0,0.1)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div 
                  className="w-10 h-10 rounded-xl flex items-center justify-center transition-transform group-hover:scale-110"
                  style={{ 
                    backgroundColor: paso.completado 
                      ? (isDark ? 'rgba(34, 197, 94, 0.2)' : '#dcfce7')
                      : (isDark ? 'rgba(249, 115, 22, 0.2)' : '#ffedd5'),
                    color: paso.completado ? '#22c55e' : '#f97316'
                  }}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <span 
                  className="text-xs font-medium px-2 py-0.5 rounded"
                  style={{ 
                    backgroundColor: paso.completado 
                      ? (isDark ? 'rgba(34, 197, 94, 0.2)' : '#dcfce7')
                      : (isDark ? 'rgba(107, 114, 128, 0.2)' : '#f3f4f6'),
                    color: paso.completado 
                      ? '#22c55e' 
                      : styles.text.secondary
                  }}
                >
                  Paso {paso.numero}
                </span>
              </div>
              
              <h3 
                className="font-semibold mb-1 flex items-center gap-1 text-sm"
                style={{ color: styles.text.primary }}
              >
                {paso.titulo}
                <ArrowRight className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity" />
              </h3>
              <p className="text-xs mb-2" style={{ color: styles.text.secondary }}>
                {paso.descripcion}
              </p>
              
              <div className="flex items-center gap-1.5 text-xs">
                {paso.completado ? (
                  <CheckCircle className="w-3 h-3" style={{ color: '#22c55e' }} />
                ) : (
                  <AlertCircle className="w-3 h-3" style={{ color: styles.text.muted }} />
                )}
                <span style={{ color: paso.completado ? '#22c55e' : styles.text.secondary }}>
                  {paso.info}
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      {/* Años disponibles */}
      {años.length > 0 && (
        <div 
          className="rounded-2xl p-6"
          style={{ ...styles.card, border: `1px solid ${styles.card.borderColor}` }}
        >
          <h2 
            className="text-lg font-semibold mb-4 flex items-center gap-2"
            style={{ color: styles.text.primary }}
          >
            <Calendar className="w-5 h-5" style={{ color: '#f97316' }} />
            Años Disponibles
          </h2>
          
          <div className="flex flex-wrap gap-2">
            {años.sort((a, b) => b - a).map(año => (
              <span 
                key={año}
                className="px-4 py-2 rounded-xl text-sm font-medium"
                style={{ 
                  backgroundColor: isDark ? 'rgba(249, 115, 22, 0.2)' : '#ffedd5',
                  color: isDark ? '#fdba74' : '#c2410c'
                }}
              >
                {año}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Estado del sistema */}
      <div 
        className="rounded-2xl p-6"
        style={{ ...styles.card, border: `1px solid ${styles.card.borderColor}` }}
      >
        <h2 
          className="text-lg font-semibold mb-4 flex items-center gap-2"
          style={{ color: styles.text.primary }}
        >
          <Zap className="w-5 h-5" style={{ color: '#f97316' }} />
          Estado del Sistema
        </h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div 
            className="flex items-center justify-between py-3 px-4 rounded-xl"
            style={{ backgroundColor: isDark ? 'rgba(55, 65, 81, 0.5)' : '#f9fafb' }}
          >
            <div className="flex items-center gap-3">
              <FileSpreadsheet className="w-5 h-5" style={{ color: styles.text.muted }} />
              <span style={{ color: styles.text.primary }}>Maestra</span>
            </div>
            {maestraCargada ? (
              <span className="flex items-center gap-1.5 text-sm" style={{ color: '#22c55e' }}>
                <CheckCircle className="w-4 h-4" />
                Cargada
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-sm" style={{ color: styles.text.muted }}>
                <XCircle className="w-4 h-4" />
                No cargada
              </span>
            )}
          </div>

          <div 
            className="flex items-center justify-between py-3 px-4 rounded-xl"
            style={{ backgroundColor: isDark ? 'rgba(55, 65, 81, 0.5)' : '#f9fafb' }}
          >
            <div className="flex items-center gap-3">
              <Server className="w-5 h-5" style={{ color: styles.text.muted }} />
              <span style={{ color: styles.text.primary }}>SFTP</span>
            </div>
            {sftpConectado ? (
              <span className="flex items-center gap-1.5 text-sm" style={{ color: '#22c55e' }}>
                <CheckCircle className="w-4 h-4" />
                Conectado
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-sm" style={{ color: styles.text.muted }}>
                <XCircle className="w-4 h-4" />
                Desconectado
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
