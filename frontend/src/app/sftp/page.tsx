'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  Server, Wifi, WifiOff, RefreshCw, Folder, FolderOpen, File, ChevronRight,
  Home, Download, Search, CheckCircle, XCircle, FileSpreadsheet, FileText,
  ArrowLeft, AlertTriangle, Calendar
} from 'lucide-react';
import { API_BASE } from '@/config/api';

interface Carpeta { nombre: string; ruta: string; fecha: string; }
interface Archivo { nombre: string; ruta: string; tamaño: number; tamaño_formateado: string; fecha: string; }
interface AñoSFTP { año: number; carpeta: string; ruta: string; }

export default function SFTPPage() {
  const [conectado, setConectado] = useState(false);
  const [servidor, setServidor] = useState<string | null>(null);
  const [conectando, setConectando] = useState(false);
  const [rutaActual, setRutaActual] = useState('');
  const [rutaPadre, setRutaPadre] = useState<string | null>(null);
  const [carpetas, setCarpetas] = useState<Carpeta[]>([]);
  const [archivos, setArchivos] = useState<Archivo[]>([]);
  const [cargando, setCargando] = useState(false);
  const [añosDisponibles, setAñosDisponibles] = useState<AñoSFTP[]>([]);
  const [mensaje, setMensaje] = useState<{ tipo: 'success' | 'error', texto: string } | null>(null);
  const [descargando, setDescargando] = useState<string | null>(null);
  const [numeroContrato, setNumeroContrato] = useState('');
  const [anoContrato, setAnoContrato] = useState('');
  const [buscando, setBuscando] = useState(false);

  useEffect(() => { if (mensaje) { const t = setTimeout(() => setMensaje(null), 5000); return () => clearTimeout(t); } }, [mensaje]);
  useEffect(() => { verificarEstado(); }, []);

  const verificarEstado = async () => {
    try {
      const res = await fetch(`${API_BASE}/sftp/estado`);
      const data = await res.json();
      setConectado(data.conectado);
      setServidor(data.servidor);
      if (data.conectado) cargarAños();
    } catch {}
  };

  const cargarAños = async () => {
    try {
      const res = await fetch(`${API_BASE}/sftp/años-disponibles`);
      const data = await res.json();
      if (data.success && data.años) {
        setAñosDisponibles(data.años);
        if (data.años.length > 0 && !anoContrato) setAnoContrato(data.años[0].año.toString());
      }
    } catch {}
  };

  const handleConectar = async () => {
    setConectando(true);
    try {
      const res = await fetch(`${API_BASE}/sftp/conectar`);
      const data = await res.json();
      if (data.success) {
        setConectado(true); setServidor(data.servidor);
        setMensaje({ tipo: 'success', texto: 'Conectado exitosamente' });
        await cargarAños();
        await navegarA('R.A-ABASTECIMIENTO RED ASISTENCIAL');
      } else setMensaje({ tipo: 'error', texto: 'Error al conectar' });
    } catch (err: any) { setMensaje({ tipo: 'error', texto: err.message || 'Error' }); }
    finally { setConectando(false); }
  };

  const handleDesconectar = async () => {
    try {
      await fetch(`${API_BASE}/sftp/desconectar`);
      setConectado(false); setServidor(null); setCarpetas([]); setArchivos([]);
      setRutaActual(''); setRutaPadre(null); setAñosDisponibles([]);
    } catch {}
  };

  const navegarA = useCallback(async (ruta: string) => {
    if (cargando) return;
    setCargando(true);
    try {
      const res = await fetch(`${API_BASE}/sftp/navegar?ruta=${encodeURIComponent(ruta)}`);
      const data = await res.json();
      if (data.success) {
        setRutaActual(data.ruta_actual); setRutaPadre(data.ruta_padre);
        setCarpetas(data.carpetas || []); setArchivos(data.archivos || []);
      }
    } catch (err: any) { setMensaje({ tipo: 'error', texto: err.message }); }
    finally { setCargando(false); }
  }, [cargando]);

  const handleBuscar = async () => {
    if (!numeroContrato.trim() || !anoContrato.trim()) { setMensaje({ tipo: 'error', texto: 'Complete los campos' }); return; }
    if (!conectado) { setMensaje({ tipo: 'error', texto: 'Conecte primero' }); return; }
    setBuscando(true);
    try {
      const res = await fetch(`${API_BASE}/sftp/buscar-contrato?numero=${encodeURIComponent(numeroContrato.trim())}&año=${encodeURIComponent(anoContrato.trim())}`);
      const data = await res.json();
      if (data.encontrado && data.ruta) {
        setMensaje({ tipo: 'success', texto: `Encontrado: ${data.carpeta}` });
        setRutaActual(data.ruta); setRutaPadre(data.ruta_padre || null);
        if (data.contenido) { setCarpetas(data.contenido.carpetas || []); setArchivos(data.contenido.archivos || []); }
      } else setMensaje({ tipo: 'error', texto: data.mensaje || 'No encontrado' });
    } catch (err: any) { setMensaje({ tipo: 'error', texto: err.message }); }
    finally { setBuscando(false); }
  };

  const handleDescargar = (archivo: Archivo) => {
    setDescargando(archivo.nombre);
    window.open(`${API_BASE}/sftp/descargar?ruta=${encodeURIComponent(archivo.ruta)}`, '_blank');
    setTimeout(() => setDescargando(null), 1000);
  };

  const getIcono = (nombre: string) => {
    const ext = nombre.split('.').pop()?.toLowerCase();
    if (['xlsx', 'xls', 'xlsb', 'xlsm'].includes(ext || '')) return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
    if (ext === 'pdf') return <FileText className="w-5 h-5 text-red-500" />;
    return <File className="w-5 h-5 text-gray-400" />;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Explorador SFTP</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">Navega y descarga archivos de GoAnywhere</p>
      </div>

      {mensaje && (
        <div className={`p-4 rounded-xl flex items-center gap-3 ${mensaje.tipo === 'success' ? 'bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20 text-green-700 dark:text-green-400' : 'bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 text-red-700 dark:text-red-400'}`}>
          {mensaje.tipo === 'success' ? <CheckCircle className="w-5 h-5" /> : <XCircle className="w-5 h-5" />}
          <p className="text-sm flex-1">{mensaje.texto}</p>
          <button onClick={() => setMensaje(null)}><XCircle className="w-4 h-4 opacity-50" /></button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="space-y-4">
          {/* Conexión */}
          <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Server className="w-5 h-5 text-orange-500" /> Conexión
            </h2>
            <div className={`p-4 rounded-xl mb-4 flex items-center gap-3 ${conectado ? 'bg-green-50 dark:bg-green-500/10' : 'bg-gray-50 dark:bg-gray-800'}`}>
              {conectado ? <Wifi className="w-6 h-6 text-green-500" /> : <WifiOff className="w-6 h-6 text-gray-400" />}
              <div>
                <p className={`font-medium ${conectado ? 'text-green-700 dark:text-green-400' : 'text-gray-500'}`}>{conectado ? 'Conectado' : 'Desconectado'}</p>
                {servidor && <p className="text-xs text-gray-500 truncate">{servidor}</p>}
              </div>
            </div>
            {conectado ? (
              <button onClick={handleDesconectar} className="w-full py-2.5 text-sm text-red-600 border border-red-200 dark:border-red-500/30 rounded-xl hover:bg-red-50 dark:hover:bg-red-500/10 font-medium">Desconectar</button>
            ) : (
              <button onClick={handleConectar} disabled={conectando} className="w-full flex items-center justify-center gap-2 py-2.5 bg-orange-500 text-white rounded-xl hover:bg-orange-600 font-medium disabled:opacity-50">
                {conectando ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Wifi className="w-4 h-4" />}
                {conectando ? 'Conectando...' : 'Conectar'}
              </button>
            )}
          </div>

          {/* Búsqueda */}
          <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
            <h2 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <Search className="w-5 h-5 text-orange-500" /> Buscar Contrato
            </h2>
            <div className="p-3 bg-orange-50 dark:bg-orange-500/10 rounded-xl mb-4 text-xs text-orange-700 dark:text-orange-400">
              <p className="font-medium mb-1">💡 Instrucciones:</p>
              <ol className="list-decimal list-inside space-y-0.5 opacity-80">
                <li>Conecte al SFTP</li>
                <li>Ingrese número de contrato</li>
                <li>Seleccione año</li>
              </ol>
            </div>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Número</label>
                <input type="text" value={numeroContrato} onChange={(e) => setNumeroContrato(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleBuscar()} placeholder="Ej: 662" className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm focus:ring-2 focus:ring-orange-500 focus:border-transparent" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Año</label>
                {añosDisponibles.length > 0 ? (
                  <select value={anoContrato} onChange={(e) => setAnoContrato(e.target.value)} className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm">
                    {añosDisponibles.map((a) => <option key={a.año} value={a.año}>{a.año}</option>)}
                  </select>
                ) : (
                  <input type="text" value={anoContrato} onChange={(e) => setAnoContrato(e.target.value)} placeholder="Ej: 2024" className="w-full px-4 py-2.5 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl text-sm" />
                )}
              </div>
              <button onClick={handleBuscar} disabled={buscando || !conectado} className="w-full flex items-center justify-center gap-2 py-2.5 bg-green-500 text-white rounded-xl hover:bg-green-600 font-medium disabled:opacity-50">
                {buscando ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                {buscando ? 'Buscando...' : 'Buscar'}
              </button>
            </div>
          </div>

          {/* Años */}
          {añosDisponibles.length > 0 && (
            <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                <Calendar className="w-5 h-5 text-orange-500" /> Años
              </h3>
              <div className="flex flex-wrap gap-2">
                {añosDisponibles.map((a) => (
                  <button key={a.año} onClick={() => navegarA(a.ruta)} className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg text-sm hover:bg-orange-100 dark:hover:bg-orange-500/20 hover:text-orange-600 dark:hover:text-orange-400 transition-colors">
                    {a.año}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Explorador */}
        <div className="lg:col-span-3">
          <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
            {/* Navegación */}
            <div className="p-4 border-b border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50">
              <div className="flex items-center gap-2">
                <button onClick={() => navegarA('R.A-ABASTECIMIENTO RED ASISTENCIAL')} disabled={!conectado || cargando} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"><Home className="w-4 h-4 text-gray-600 dark:text-gray-400" /></button>
                <button onClick={() => rutaPadre && navegarA(rutaPadre)} disabled={!rutaPadre || cargando} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50"><ArrowLeft className="w-4 h-4 text-gray-600 dark:text-gray-400" /></button>
                <div className="flex-1 flex items-center gap-2 px-3 py-2 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 min-w-0">
                  <Folder className="w-4 h-4 text-orange-500 flex-shrink-0" />
                  <span className="text-sm text-gray-700 dark:text-gray-300 truncate">{rutaActual || 'Sin conexión'}</span>
                </div>
                <button onClick={() => rutaActual && navegarA(rutaActual)} disabled={!conectado || cargando} className="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg disabled:opacity-50">
                  <RefreshCw className={`w-4 h-4 text-gray-600 dark:text-gray-400 ${cargando ? 'animate-spin' : ''}`} />
                </button>
              </div>
            </div>

            {/* Contenido */}
            <div className="min-h-[400px] max-h-[500px] overflow-auto">
              {!conectado ? (
                <div className="flex flex-col items-center justify-center h-[400px] text-gray-400">
                  <WifiOff className="w-16 h-16 mb-4 opacity-30" />
                  <p>Conecte al servidor SFTP</p>
                </div>
              ) : cargando ? (
                <div className="flex items-center justify-center h-[400px]">
                  <RefreshCw className="w-8 h-8 animate-spin text-orange-500" />
                </div>
              ) : carpetas.length === 0 && archivos.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-[400px] text-gray-400">
                  <FolderOpen className="w-16 h-16 mb-4 opacity-30" />
                  <p>Carpeta vacía</p>
                </div>
              ) : (
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {carpetas.map((c) => (
                    <div key={c.ruta} onClick={() => navegarA(c.ruta)} className="flex items-center gap-4 px-5 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 cursor-pointer group">
                      <div className="w-10 h-10 bg-orange-100 dark:bg-orange-500/20 rounded-xl flex items-center justify-center">
                        <Folder className="w-5 h-5 text-orange-500" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white truncate group-hover:text-orange-600 dark:group-hover:text-orange-400">{c.nombre}</p>
                        <p className="text-xs text-gray-500">{c.fecha}</p>
                      </div>
                      <ChevronRight className="w-4 h-4 text-gray-400 group-hover:text-orange-500" />
                    </div>
                  ))}
                  {archivos.map((a) => (
                    <div key={a.ruta} className="flex items-center gap-4 px-5 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                      <div className="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
                        {getIcono(a.nombre)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 dark:text-white truncate">{a.nombre}</p>
                        <p className="text-xs text-gray-500">{a.tamaño_formateado} • {a.fecha}</p>
                      </div>
                      <button onClick={() => handleDescargar(a)} disabled={descargando === a.nombre} className="flex items-center gap-2 px-3 py-1.5 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600 disabled:opacity-50">
                        {descargando === a.nombre ? <RefreshCw className="w-3 h-3 animate-spin" /> : <Download className="w-3 h-3" />}
                        <span className="hidden sm:inline">Descargar</span>
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {conectado && (carpetas.length > 0 || archivos.length > 0) && (
              <div className="px-5 py-2 border-t border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-800/50 text-xs text-gray-500">
                {carpetas.length} carpetas, {archivos.length} archivos
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
