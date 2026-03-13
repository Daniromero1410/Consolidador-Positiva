'use client';

import { useState } from 'react';
import {
    FileCheck, Search, Download, Loader2, CheckCircle, XCircle,
    AlertTriangle, Shield, Scale, Gavel, ChevronDown, FileText,
    User, Hash
} from 'lucide-react';
import { API_BASE } from '@/config/api';

// ══════════════════════════════════════════════════════════════
// TIPOS
// ══════════════════════════════════════════════════════════════

interface CertificadoResult {
    tipo: string;
    nombre: string;
    estado: 'sin_antecedentes' | 'con_antecedentes' | 'error' | 'pendiente' | 'procesando';
    mensaje?: string;
    pdf_url?: string;
    screenshot_url?: string;
}

const TIPOS_DOCUMENTO = [
    { value: 'CC', label: 'Cédula de Ciudadanía' },
    { value: 'CE', label: 'Cédula de Extranjería' },
    { value: 'TI', label: 'Tarjeta de Identidad' },
    { value: 'PA', label: 'Pasaporte' },
    { value: 'NIT', label: 'NIT' },
];

const CERTIFICADOS_DISPONIBLES = [
    {
        id: 'medidas',
        nombre: 'Medidas Correctivas',
        descripcion: 'Registro Nacional de Medidas Correctivas (RNMC)',
        entidad: 'Policía Nacional',
        icon: Shield,
        color: '#3b82f6',
    },
    {
        id: 'disciplinarios',
        nombre: 'Antecedentes Judiciales',
        descripcion: 'Consulta de antecedentes judiciales',
        entidad: 'Policía Nacional - DIJIN',
        icon: Gavel,
        color: '#8b5cf6',
    },
    {
        id: 'fiscales',
        nombre: 'Antecedentes Fiscales',
        descripcion: 'Certificado de antecedentes de responsabilidad fiscal',
        entidad: 'Contraloría General',
        icon: Scale,
        color: '#10b981',
    },
];

// ══════════════════════════════════════════════════════════════
// HOOK DE TEMA
// ══════════════════════════════════════════════════════════════

function useTheme() {
    const [theme] = useState<'light' | 'dark'>(() => {
        if (typeof window !== 'undefined') {
            return (localStorage.getItem('theme') as 'dark' | 'light') || 'light';
        }
        return 'light';
    });
    return theme;
}

// ══════════════════════════════════════════════════════════════
// COMPONENTE PRINCIPAL
// ══════════════════════════════════════════════════════════════

export default function CertificadosPage() {
    const theme = useTheme();
    const isDark = theme === 'dark';

    const [tipoDoc, setTipoDoc] = useState('CC');
    const [numDoc, setNumDoc] = useState('');
    const [certificadosSeleccionados, setCertificadosSeleccionados] = useState<string[]>(
        CERTIFICADOS_DISPONIBLES.map(c => c.id)
    );
    const [resultados, setResultados] = useState<CertificadoResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const styles = {
        card: {
            backgroundColor: isDark ? '#1f2937' : '#ffffff',
            borderColor: isDark ? '#374151' : '#e5e7eb',
        },
        text: {
            primary: isDark ? '#ffffff' : '#111827',
            secondary: isDark ? '#9ca3af' : '#6b7280',
        },
        input: {
            backgroundColor: isDark ? '#111827' : '#f9fafb',
            borderColor: isDark ? '#374151' : '#d1d5db',
            color: isDark ? '#ffffff' : '#111827',
        },
    };

    const toggleCertificado = (id: string) => {
        setCertificadosSeleccionados(prev =>
            prev.includes(id) ? prev.filter(c => c !== id) : [...prev, id]
        );
    };

    const handleConsultar = async () => {
        if (!numDoc.trim()) {
            setError('Ingrese el número de documento');
            return;
        }
        if (certificadosSeleccionados.length === 0) {
            setError('Seleccione al menos un certificado');
            return;
        }

        setError('');
        setLoading(true);

        // Inicializar resultados como "procesando"
        setResultados(
            certificadosSeleccionados.map(id => {
                const cert = CERTIFICADOS_DISPONIBLES.find(c => c.id === id)!;
                return {
                    tipo: id,
                    nombre: cert.nombre,
                    estado: 'procesando',
                };
            })
        );

        try {
            const res = await fetch(`${API_BASE}/certificados/consultar`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tipo_documento: tipoDoc,
                    numero_documento: numDoc.trim(),
                    certificados: certificadosSeleccionados,
                }),
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Error al consultar certificados');
            }

            const data = await res.json();

            // Mapear respuesta
            const nuevosResultados: CertificadoResult[] = certificadosSeleccionados.map(id => {
                const cert = CERTIFICADOS_DISPONIBLES.find(c => c.id === id)!;
                const resultado = data[id];
                return {
                    tipo: id,
                    nombre: cert.nombre,
                    estado: resultado?.estado || 'error',
                    mensaje: resultado?.mensaje,
                    pdf_url: resultado?.pdf_url,
                    screenshot_url: resultado?.screenshot_url,
                };
            });

            setResultados(nuevosResultados);
        } catch (err: any) {
            setError(err.message || 'Error de conexión');
            setResultados(prev =>
                prev.map(r => ({ ...r, estado: 'error' as const, mensaje: 'Error de conexión' }))
            );
        } finally {
            setLoading(false);
        }
    };

    const getEstadoBadge = (estado: CertificadoResult['estado']) => {
        switch (estado) {
            case 'sin_antecedentes':
                return { icon: CheckCircle, text: 'Sin antecedentes', color: '#22c55e', bg: isDark ? 'rgba(34,197,94,0.1)' : '#dcfce7' };
            case 'con_antecedentes':
                return { icon: AlertTriangle, text: 'Con antecedentes', color: '#ef4444', bg: isDark ? 'rgba(239,68,68,0.1)' : '#fef2f2' };
            case 'procesando':
                return { icon: Loader2, text: 'Consultando...', color: '#f97316', bg: isDark ? 'rgba(249,115,22,0.1)' : '#fff7ed' };
            case 'error':
                return { icon: XCircle, text: 'Error', color: '#ef4444', bg: isDark ? 'rgba(239,68,68,0.1)' : '#fef2f2' };
            default:
                return { icon: FileCheck, text: 'Pendiente', color: '#6b7280', bg: isDark ? 'rgba(107,114,128,0.1)' : '#f3f4f6' };
        }
    };

    return (
        <div className="space-y-6">
            {/* Header */}
            <div>
                <h1 className="text-2xl font-bold" style={{ color: styles.text.primary }}>
                    Descarga de Certificados
                </h1>
                <p style={{ color: styles.text.secondary }} className="mt-1 text-sm">
                    Consulta automatizada de certificados gubernamentales · Sin necesidad de login
                </p>
            </div>

            {/* Formulario */}
            <div
                className="rounded-2xl p-6"
                style={{ ...styles.card, border: `1px solid ${styles.card.borderColor}` }}
            >
                <h2
                    className="text-lg font-semibold mb-4 flex items-center gap-2"
                    style={{ color: styles.text.primary }}
                >
                    <Search className="w-5 h-5" style={{ color: '#f97316' }} />
                    Datos de Consulta
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                    {/* Tipo de documento */}
                    <div>
                        <label className="block text-sm font-medium mb-1.5" style={{ color: styles.text.secondary }}>
                            <User className="w-3.5 h-3.5 inline mr-1" />
                            Tipo de Documento
                        </label>
                        <div className="relative">
                            <select
                                value={tipoDoc}
                                onChange={(e) => setTipoDoc(e.target.value)}
                                className="w-full px-4 py-2.5 rounded-xl text-sm appearance-none outline-none transition-all"
                                style={{ ...styles.input, border: `1px solid ${styles.input.borderColor}` }}
                            >
                                {TIPOS_DOCUMENTO.map(t => (
                                    <option key={t.value} value={t.value}>{t.label}</option>
                                ))}
                            </select>
                            <ChevronDown
                                className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none"
                                style={{ color: styles.text.secondary }}
                            />
                        </div>
                    </div>

                    {/* Número de documento */}
                    <div>
                        <label className="block text-sm font-medium mb-1.5" style={{ color: styles.text.secondary }}>
                            <Hash className="w-3.5 h-3.5 inline mr-1" />
                            Número de Documento
                        </label>
                        <input
                            type="text"
                            value={numDoc}
                            onChange={(e) => setNumDoc(e.target.value.replace(/[^0-9]/g, ''))}
                            placeholder="Ej: 1234567890"
                            className="w-full px-4 py-2.5 rounded-xl text-sm outline-none transition-all"
                            style={{ ...styles.input, border: `1px solid ${styles.input.borderColor}` }}
                            onFocus={(e) => e.target.style.borderColor = '#f97316'}
                            onBlur={(e) => e.target.style.borderColor = styles.input.borderColor}
                        />
                    </div>
                </div>

                {/* Certificados disponibles */}
                <div className="mb-6">
                    <label className="block text-sm font-medium mb-3" style={{ color: styles.text.secondary }}>
                        Certificados a consultar
                    </label>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                        {CERTIFICADOS_DISPONIBLES.map(cert => {
                            const Icon = cert.icon;
                            const selected = certificadosSeleccionados.includes(cert.id);
                            return (
                                <button
                                    key={cert.id}
                                    onClick={() => toggleCertificado(cert.id)}
                                    className="p-4 rounded-xl text-left transition-all duration-200"
                                    style={{
                                        backgroundColor: selected
                                            ? (isDark ? `${cert.color}15` : `${cert.color}10`)
                                            : (isDark ? '#111827' : '#f9fafb'),
                                        border: `2px solid ${selected ? cert.color : (isDark ? '#374151' : '#e5e7eb')}`,
                                    }}
                                >
                                    <div className="flex items-start gap-3">
                                        <div
                                            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                                            style={{ backgroundColor: `${cert.color}20`, color: cert.color }}
                                        >
                                            <Icon className="w-4 h-4" />
                                        </div>
                                        <div className="min-w-0">
                                            <p className="font-medium text-sm" style={{ color: styles.text.primary }}>
                                                {cert.nombre}
                                            </p>
                                            <p className="text-xs mt-0.5" style={{ color: styles.text.secondary }}>
                                                {cert.entidad}
                                            </p>
                                        </div>
                                    </div>
                                </button>
                            );
                        })}
                    </div>
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

                {/* Botón consultar */}
                <button
                    onClick={handleConsultar}
                    disabled={loading || !numDoc.trim()}
                    className="w-full py-3 rounded-xl text-white font-medium text-sm transition-all duration-200 flex items-center justify-center gap-2"
                    style={{
                        background: loading ? '#9ca3af' : 'linear-gradient(135deg, #f97316, #ea580c)',
                        opacity: !numDoc.trim() ? 0.6 : 1,
                        cursor: loading ? 'not-allowed' : 'pointer',
                    }}
                >
                    {loading ? (
                        <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Consultando certificados...
                        </>
                    ) : (
                        <>
                            <Search className="w-4 h-4" />
                            Consultar Certificados
                        </>
                    )}
                </button>
            </div>

            {/* Resultados */}
            {resultados.length > 0 && (
                <div
                    className="rounded-2xl p-6"
                    style={{ ...styles.card, border: `1px solid ${styles.card.borderColor}` }}
                >
                    <h2
                        className="text-lg font-semibold mb-4 flex items-center gap-2"
                        style={{ color: styles.text.primary }}
                    >
                        <FileText className="w-5 h-5" style={{ color: '#f97316' }} />
                        Resultados
                    </h2>

                    <div className="space-y-3">
                        {resultados.map(resultado => {
                            const badge = getEstadoBadge(resultado.estado);
                            const BadgeIcon = badge.icon;
                            const cert = CERTIFICADOS_DISPONIBLES.find(c => c.id === resultado.tipo);
                            const CertIcon = cert?.icon || FileCheck;

                            return (
                                <div
                                    key={resultado.tipo}
                                    className="flex items-center justify-between p-4 rounded-xl"
                                    style={{ backgroundColor: isDark ? '#111827' : '#f9fafb' }}
                                >
                                    <div className="flex items-center gap-3">
                                        <div
                                            className="w-10 h-10 rounded-lg flex items-center justify-center"
                                            style={{ backgroundColor: `${cert?.color || '#6b7280'}20`, color: cert?.color }}
                                        >
                                            <CertIcon className="w-5 h-5" />
                                        </div>
                                        <div>
                                            <p className="font-medium text-sm" style={{ color: styles.text.primary }}>
                                                {resultado.nombre}
                                            </p>
                                            {resultado.mensaje && (
                                                <p className="text-xs mt-0.5" style={{ color: styles.text.secondary }}>
                                                    {resultado.mensaje}
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    <div className="flex items-center gap-2 sm:gap-3">
                                        <span
                                            className="hidden sm:flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-lg"
                                            style={{ backgroundColor: badge.bg, color: badge.color }}
                                        >
                                            <BadgeIcon className={`w-3.5 h-3.5 ${resultado.estado === 'procesando' ? 'animate-spin' : ''}`} />
                                            {badge.text}
                                        </span>

                                        {resultado.screenshot_url && (
                                            <a
                                                href={resultado.screenshot_url.startsWith('http') ? resultado.screenshot_url : API_BASE.replace('/api', '') + resultado.screenshot_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                                                style={{ backgroundColor: isDark ? 'rgba(59,130,246,0.1)' : '#eff6ff', color: '#3b82f6' }}
                                            >
                                                <Search className="w-3.5 h-3.5" />
                                                Captura
                                            </a>
                                        )}

                                        {resultado.pdf_url && (
                                            <a
                                                href={resultado.pdf_url.startsWith('http') ? resultado.pdf_url : API_BASE.replace('/api', '') + resultado.pdf_url}
                                                target="_blank"
                                                rel="noopener noreferrer"
                                                className="flex items-center gap-1 text-xs font-medium px-3 py-1.5 rounded-lg transition-colors"
                                                style={{ backgroundColor: isDark ? 'rgba(249,115,22,0.1)' : '#fff7ed', color: '#f97316' }}
                                            >
                                                <Download className="w-3.5 h-3.5" />
                                                PDF
                                            </a>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Info */}
            <div
                className="rounded-2xl p-4 text-xs"
                style={{
                    backgroundColor: isDark ? 'rgba(59,130,246,0.05)' : '#eff6ff',
                    border: `1px solid ${isDark ? 'rgba(59,130,246,0.15)' : '#dbeafe'}`,
                    color: isDark ? '#93c5fd' : '#2563eb'
                }}
            >
                <p className="font-medium mb-1">ℹ️ Información</p>
                <p>Los certificados se consultan directamente en las páginas oficiales del gobierno colombiano.
                    La consulta puede tardar entre 10-30 segundos por certificado. Los PDFs generados se almacenan temporalmente.</p>
            </div>
        </div>
    );
}
