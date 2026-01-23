'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import {
  Play,
  Square,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileSpreadsheet,
  Download,
  HardDrive,
  Search,
  Clock,
  Activity,
  TrendingUp,
  Zap,
  Filter
} from 'lucide-react';
import Link from 'next/link';
import { API_BASE } from '@/config/api';

interface LogEntry {
  timestamp: string;
  tipo: string;
  mensaje: string;
}

interface ContratoInfo {
  numero: string;
  razon_social: string;
}

// Componente de Log
const LogLine = ({ log }: { log: LogEntry }) => {
  const getLogStyle = (mensaje: string) => {
    const msg = mensaje.toLowerCase();
    if (msg.includes('error') || msg.includes('❌')) return 'text-red-400';
    if (msg.includes('⚠') || msg.includes('warning')) return 'text-yellow-400';
    if (msg.includes('✅') || msg.includes('éxito')) return 'text-green-400';
    if (msg.includes('descargando') || msg.includes('⬇')) return 'text-blue-400';
    if (msg.includes('contrato [') || msg.includes('📋')) return 'text-orange-400 font-medium';
    if (msg.includes('navegando') || msg.includes('📂')) return 'text-cyan-400';
    if (msg.includes('procesando') || msg.includes('⚙')) return 'text-purple-400';
    if (msg.includes('servicios extraídos') || msg.includes('servicios en')) return 'text-emerald-400';
    return 'text-gray-400';
  };

  return (
    <div className="flex gap-3 py-1.5 px-4 hover:bg-white/5 font-mono text-xs">
      <span className="text-gray-600 flex-shrink-0">{log.timestamp}</span>
      <span className={getLogStyle(log.mensaje)}>{log.mensaje}</span>
    </div>
  );
};

export default function ProcesarPage() {
  const [maestraCargada, setMaestraCargada] = useState<boolean | null>(null);
  const [maestraArchivo, setMaestraArchivo] = useState('');
  const [maestraContratos, setMaestraContratos] = useState(0);
  const [anos, setAnos] = useState<{año: number, cantidad_contratos: number}[]>([]);
  const [contratos, setContratos] = useState<ContratoInfo[]>([]);
  const [anoSeleccionado, setAnoSeleccionado] = useState<number | null>(null);
  const [contratoSeleccionado, setContratoSeleccionado] = useState<string | null>(null);
  const [procesarTodo, setProcesarTodo] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobEstado, setJobEstado] = useState<string | null>(null);
  const [progreso, setProgreso] = useState(0);
  const [mensaje, setMensaje] = useState('');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [archivosGenerados, setArchivosGenerados] = useState<string[]>([]);
  const [iniciando, setIniciando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filtroTexto, setFiltroTexto] = useState('');
  const [autoScroll, setAutoScroll] = useState(true);
  
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const lastLogIndexRef = useRef(0);

  const stats = useMemo(() => {
    let contratosActual = 0, totalContratos = 0, exitosos = 0, errores = 0, servicios = 0;
    logs.forEach(log => {
      const msg = log.mensaje;
      const contratoMatch = msg.match(/CONTRATO \[(\d+)\/(\d+)\]/);
      if (contratoMatch) { contratosActual = parseInt(contratoMatch[1]); totalContratos = parseInt(contratoMatch[2]); }
      if (msg.includes('✅') && msg.includes('servicios')) { exitosos++; const m = msg.match(/([\d,]+) servicios/); if (m) servicios += parseInt(m[1].replace(/,/g, '')); }
      if (msg.includes('❌') || msg.includes('ERROR')) errores++;
    });
    return { contratosActual, totalContratos, exitosos, errores, servicios };
  }, [logs]);

  useEffect(() => {
    const cargar = async () => {
      try {
        const res = await fetch(`${API_BASE}/maestra/estado`);
        const data = await res.json();
        setMaestraCargada(data.cargada);
        setMaestraArchivo(data.archivo || '');
        setMaestraContratos(data.total_contratos || 0);
        if (data.cargada && data.años_disponibles) {
          setAnos(data.años_disponibles.map((año: number) => ({ año, cantidad_contratos: 0 })));
          fetch(`${API_BASE}/maestra/años`).then(r => r.json()).then(d => d.años && setAnos(d.años)).catch(() => {});
        }
      } catch { setMaestraCargada(false); }
    };
    cargar();
  }, []);

  useEffect(() => {
    if (!anoSeleccionado) { setContratos([]); return; }
    fetch(`${API_BASE}/maestra/contratos?año=${anoSeleccionado}`)
      .then(r => r.json()).then(data => setContratos(data.contratos || [])).catch(() => setContratos([]));
    setContratoSeleccionado(null);
  }, [anoSeleccionado]);

  const iniciarPolling = useCallback((jId: string) => {
    if (pollingRef.current) clearInterval(pollingRef.current);
    lastLogIndexRef.current = 0;
    pollingRef.current = setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/procesar/logs/${jId}?desde=${lastLogIndexRef.current}`);
        const data = await res.json();
        if (data.logs?.length > 0) { setLogs(prev => [...prev, ...data.logs]); lastLogIndexRef.current += data.logs.length; }
        setProgreso(data.progreso); setMensaje(data.mensaje); setJobEstado(data.estado);
        if (['completado', 'error', 'cancelado'].includes(data.estado)) {
          clearInterval(pollingRef.current!); pollingRef.current = null;
          if (data.archivos_generados) setArchivosGenerados(data.archivos_generados);
        }
      } catch {}
    }, 500);
  }, []);

  useEffect(() => {
    if (autoScroll && logsContainerRef.current) logsContainerRef.current.scrollTop = logsContainerRef.current.scrollHeight;
  }, [logs, autoScroll]);

  useEffect(() => { return () => { if (pollingRef.current) clearInterval(pollingRef.current); }; }, []);

  const logsFiltrados = useMemo(() => {
    if (!filtroTexto) return logs;
    return logs.filter(log => log.mensaje.toLowerCase().includes(filtroTexto.toLowerCase()));
  }, [logs, filtroTexto]);

  const handleIniciar = async () => {
    setError(null); setIniciando(true); setLogs([]); setArchivosGenerados([]); setProgreso(0); lastLogIndexRef.current = 0;
    try {
      const params: any = {};
      if (procesarTodo) params.procesar_todo = true;
      else if (contratoSeleccionado && anoSeleccionado) { params.año = anoSeleccionado; params.numero_contrato = contratoSeleccionado; }
      else if (anoSeleccionado) params.año = anoSeleccionado;
      else { setError('Seleccione un año o marque "Procesar todos"'); setIniciando(false); return; }
      const res = await fetch(`${API_BASE}/procesar`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) });
      const data = await res.json();
      if (data.success && data.job_id) { setJobId(data.job_id); setJobEstado('en_proceso'); iniciarPolling(data.job_id); }
      else setError(data.detail || 'Error al iniciar');
    } catch (err: any) { setError(err.message || 'Error'); }
    finally { setIniciando(false); }
  };

  const handleCancelar = async () => {
    if (!jobId) return;
    try { await fetch(`${API_BASE}/procesar/cancelar/${jobId}`, { method: 'DELETE' }); setJobEstado('cancelado'); if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; } } catch {}
  };

  if (maestraCargada === null) return <div className="flex items-center justify-center h-[60vh]"><RefreshCw className="w-8 h-8 animate-spin text-orange-500" /></div>;

  if (!maestraCargada) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center">
          <div className="w-16 h-16 bg-yellow-100 dark:bg-yellow-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileSpreadsheet className="w-8 h-8 text-yellow-500" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">Maestra no cargada</h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">Debe cargar una maestra antes de procesar</p>
          <Link href="/maestra" className="inline-flex items-center gap-2 px-5 py-2.5 bg-orange-500 text-white rounded-xl hover:bg-orange-600 font-medium">
            Ir a cargar maestra
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Procesar Contratos</h1>
          <div className="flex items-center gap-2 mt-1 text-sm text-gray-500 dark:text-gray-400">
            <HardDrive className="w-4 h-4 text-orange-500" />
            <span>{maestraArchivo}</span>
            <span className="text-gray-300 dark:text-gray-600">•</span>
            <span className="font-medium text-gray-700 dark:text-gray-300">{maestraContratos} contratos</span>
          </div>
        </div>
        
        {/* Estadísticas mini */}
        {jobEstado && (
          <div className="hidden lg:flex items-center gap-4 bg-white dark:bg-gray-900 rounded-xl p-3 border border-gray-200 dark:border-gray-800">
            <div className="text-center px-3">
              <p className="text-lg font-bold text-gray-900 dark:text-white">{stats.contratosActual}<span className="text-gray-400">/{stats.totalContratos}</span></p>
              <p className="text-xs text-gray-500">Contratos</p>
            </div>
            <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
            <div className="text-center px-3">
              <p className="text-lg font-bold text-green-500">{stats.exitosos}</p>
              <p className="text-xs text-gray-500">Éxitos</p>
            </div>
            <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
            <div className="text-center px-3">
              <p className="text-lg font-bold text-red-500">{stats.errores}</p>
              <p className="text-xs text-gray-500">Errores</p>
            </div>
            <div className="w-px h-8 bg-gray-200 dark:bg-gray-700" />
            <div className="text-center px-3">
              <p className="text-lg font-bold text-blue-500">{stats.servicios.toLocaleString()}</p>
              <p className="text-xs text-gray-500">Servicios</p>
            </div>
          </div>
        )}
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-500" />
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
          <button onClick={() => setError(null)} className="ml-auto"><XCircle className="w-4 h-4 text-red-400" /></button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Panel configuración */}
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5 text-orange-500" />
              Configuración
            </h2>

            <label className="flex items-center gap-3 p-3 rounded-xl border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer mb-4">
              <input type="checkbox" checked={procesarTodo} onChange={(e) => { setProcesarTodo(e.target.checked); if (e.target.checked) { setAnoSeleccionado(null); setContratoSeleccionado(null); } }} disabled={jobEstado === 'en_proceso'} className="w-4 h-4 text-orange-500 rounded border-gray-300 focus:ring-orange-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Procesar todos</span>
            </label>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Año</label>
              <select value={anoSeleccionado || ''} onChange={(e) => setAnoSeleccionado(e.target.value ? Number(e.target.value) : null)} disabled={procesarTodo || jobEstado === 'en_proceso'} className="w-full px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl disabled:opacity-50 focus:ring-2 focus:ring-orange-500 focus:border-transparent">
                <option value="">Seleccione año</option>
                {anos.map((a) => <option key={a.año} value={a.año}>{a.año} ({a.cantidad_contratos})</option>)}
              </select>
            </div>

            <div className="mb-5">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Contrato</label>
              <select value={contratoSeleccionado || ''} onChange={(e) => setContratoSeleccionado(e.target.value || null)} disabled={procesarTodo || !anoSeleccionado || jobEstado === 'en_proceso'} className="w-full px-4 py-2.5 text-sm bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl disabled:opacity-50 focus:ring-2 focus:ring-orange-500 focus:border-transparent">
                <option value="">Todos del año</option>
                {contratos.map((c) => <option key={c.numero} value={c.numero}>{c.numero} - {c.razon_social?.substring(0, 18)}</option>)}
              </select>
            </div>

            {jobEstado === 'en_proceso' ? (
              <button onClick={handleCancelar} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-red-500 text-white rounded-xl hover:bg-red-600 font-medium">
                <Square className="w-4 h-4" /> Detener
              </button>
            ) : (
              <button onClick={handleIniciar} disabled={iniciando || (!procesarTodo && !anoSeleccionado)} className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-orange-500 text-white rounded-xl hover:bg-orange-600 font-medium disabled:opacity-50 disabled:cursor-not-allowed">
                {iniciando ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                {iniciando ? 'Iniciando...' : 'Iniciar Procesamiento'}
              </button>
            )}
          </div>

          {archivosGenerados.length > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Download className="w-5 h-5 text-green-500" />
                Archivos ({archivosGenerados.length})
              </h3>
              <div className="space-y-2 max-h-40 overflow-auto">
                {archivosGenerados.map((a) => (
                  <a key={a} href={`${API_BASE}/descargas/archivo/${a}`} className="flex items-center gap-2 p-2.5 rounded-xl bg-green-50 dark:bg-green-500/10 text-green-700 dark:text-green-400 text-xs hover:bg-green-100 dark:hover:bg-green-500/20" download>
                    <FileSpreadsheet className="w-4 h-4" />
                    <span className="truncate flex-1">{a}</span>
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Panel logs */}
        <div className="lg:col-span-3">
          <div className="bg-gray-900 rounded-2xl overflow-hidden border border-gray-800 h-[calc(100vh-280px)] flex flex-col">
            {/* Header logs */}
            <div className="px-5 py-4 border-b border-gray-800 bg-gray-800/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${jobEstado === 'en_proceso' ? 'bg-green-400 animate-pulse' : jobEstado === 'completado' ? 'bg-green-400' : jobEstado === 'error' ? 'bg-red-400' : 'bg-gray-500'}`} />
                  <span className="text-white font-medium">Terminal</span>
                  <span className="text-gray-500 text-sm">{logsFiltrados.length} líneas</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="relative">
                    <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <input type="text" value={filtroTexto} onChange={(e) => setFiltroTexto(e.target.value)} placeholder="Filtrar..." className="pl-9 pr-4 py-2 text-sm bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-500 w-40 focus:outline-none focus:border-orange-500" />
                  </div>
                  <button onClick={() => setAutoScroll(!autoScroll)} className={`px-3 py-2 text-xs rounded-lg font-medium ${autoScroll ? 'bg-orange-500 text-white' : 'bg-gray-800 text-gray-400'}`}>
                    Auto-scroll
                  </button>
                </div>
              </div>

              {jobEstado && (
                <div className="mt-4">
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div className={`h-full rounded-full transition-all ${jobEstado === 'completado' ? 'bg-green-500' : jobEstado === 'error' ? 'bg-red-500' : 'bg-gradient-to-r from-orange-500 to-yellow-500'}`} style={{ width: `${progreso}%` }} />
                    </div>
                    <span className="text-white font-mono text-sm">{Math.round(progreso)}%</span>
                  </div>
                </div>
              )}
            </div>

            {/* Contenido logs */}
            <div ref={logsContainerRef} className="flex-1 overflow-auto">
              {logs.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <Clock className="w-16 h-16 mb-4 opacity-20" />
                  <p className="text-lg">Esperando procesamiento...</p>
                  <p className="text-sm text-gray-600">Configure las opciones y presione "Iniciar"</p>
                </div>
              ) : (
                <div className="py-2">{logsFiltrados.map((log, i) => <LogLine key={i} log={log} />)}</div>
              )}
            </div>

            {mensaje && jobEstado && (
              <div className={`px-5 py-3 border-t border-gray-800 text-sm flex items-center gap-2 ${jobEstado === 'completado' ? 'bg-green-900/20 text-green-400' : jobEstado === 'error' ? 'bg-red-900/20 text-red-400' : 'bg-gray-800/50 text-gray-400'}`}>
                {jobEstado === 'en_proceso' && <RefreshCw className="w-4 h-4 animate-spin" />}
                {jobEstado === 'completado' && <CheckCircle className="w-4 h-4" />}
                {jobEstado === 'error' && <XCircle className="w-4 h-4" />}
                <span className="truncate">{mensaje}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
