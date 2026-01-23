'use client';

import { useState, useEffect } from 'react';
import {
  Download,
  FileSpreadsheet,
  Trash2,
  RefreshCw,
  File,
  FileText,
  Calendar,
  HardDrive,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  FolderOpen
} from 'lucide-react';
import { API_BASE } from '@/config/api';

interface Archivo {
  nombre: string;
  tamaño: number;
  tamaño_formateado: string;
  fecha_modificacion: string;
}

export default function DescargasPage() {
  const [archivos, setArchivos] = useState<Archivo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [filtro, setFiltro] = useState('');
  const [eliminando, setEliminando] = useState<string | null>(null);

  const cargarArchivos = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/descargas/listar`);
      const data = await res.json();
      if (data.success) {
        setArchivos(data.archivos || []);
      }
    } catch (err) {
      setError('Error al cargar archivos');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarArchivos();
  }, []);

  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => { setError(null); setSuccess(null); }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  const handleDescargar = (nombre: string) => {
    window.open(`${API_BASE}/descargas/archivo/${nombre}`, '_blank');
  };

  const handleEliminar = async (nombre: string) => {
    if (!confirm(`¿Eliminar ${nombre}?`)) return;
    
    setEliminando(nombre);
    try {
      const res = await fetch(`${API_BASE}/descargas/archivo/${nombre}`, { method: 'DELETE' });
      if (res.ok) {
        setArchivos(prev => prev.filter(a => a.nombre !== nombre));
        setSuccess('Archivo eliminado');
      } else {
        setError('Error al eliminar');
      }
    } catch {
      setError('Error al eliminar');
    } finally {
      setEliminando(null);
    }
  };

  const getIcono = (nombre: string) => {
    const ext = nombre.split('.').pop()?.toLowerCase();
    if (['xlsx', 'xls', 'xlsb', 'xlsm', 'csv'].includes(ext || '')) {
      return <FileSpreadsheet className="w-5 h-5 text-green-500" />;
    }
    if (ext === 'pdf') {
      return <FileText className="w-5 h-5 text-red-500" />;
    }
    return <File className="w-5 h-5 text-gray-500" />;
  };

  const archivosFiltrados = archivos.filter(a => 
    a.nombre.toLowerCase().includes(filtro.toLowerCase())
  );

  const totalTamaño = archivos.reduce((acc, a) => acc + a.tamaño, 0);
  const formatearTamaño = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Descargas</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Archivos generados por el consolidador
          </p>
        </div>
        <button
          onClick={cargarArchivos}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Alertas */}
      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-500/10 border border-red-200 dark:border-red-500/20 rounded-xl flex items-center gap-3">
          <XCircle className="w-5 h-5 text-red-500" />
          <p className="text-sm text-red-700 dark:text-red-400">{error}</p>
        </div>
      )}
      {success && (
        <div className="p-4 bg-green-50 dark:bg-green-500/10 border border-green-200 dark:border-green-500/20 rounded-xl flex items-center gap-3">
          <CheckCircle className="w-5 h-5 text-green-500" />
          <p className="text-sm text-green-700 dark:text-green-400">{success}</p>
        </div>
      )}

      {/* Estadísticas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-orange-100 dark:bg-orange-500/20 rounded-xl flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5 text-orange-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{archivos.length}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Archivos</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-blue-100 dark:bg-blue-500/20 rounded-xl flex items-center justify-center">
              <HardDrive className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{formatearTamaño(totalTamaño)}</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Tamaño total</p>
            </div>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-900 rounded-2xl p-5 border border-gray-200 dark:border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-11 h-11 bg-green-100 dark:bg-green-500/20 rounded-xl flex items-center justify-center">
              <Download className="w-5 h-5 text-green-500" />
            </div>
            <div>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">Listo</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">Para descargar</p>
            </div>
          </div>
        </div>
      </div>

      {/* Lista de archivos */}
      <div className="bg-white dark:bg-gray-900 rounded-2xl border border-gray-200 dark:border-gray-800 overflow-hidden">
        {/* Barra de búsqueda */}
        <div className="p-4 border-b border-gray-200 dark:border-gray-800">
          <div className="relative max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              value={filtro}
              onChange={(e) => setFiltro(e.target.value)}
              placeholder="Buscar archivos..."
              className="w-full pl-10 pr-4 py-2 bg-gray-50 dark:bg-gray-800 border-0 rounded-xl text-sm focus:ring-2 focus:ring-orange-500"
            />
          </div>
        </div>

        {/* Contenido */}
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <RefreshCw className="w-8 h-8 animate-spin text-orange-500" />
          </div>
        ) : archivosFiltrados.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-500">
            <FolderOpen className="w-16 h-16 mb-4 opacity-30" />
            <p className="text-lg font-medium">No hay archivos</p>
            <p className="text-sm text-gray-400 mt-1">
              {filtro ? 'No se encontraron resultados' : 'Los archivos generados aparecerán aquí'}
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {archivosFiltrados.map((archivo) => (
              <div
                key={archivo.nombre}
                className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
              >
                <div className="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-xl flex items-center justify-center">
                  {getIcono(archivo.nombre)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white truncate">
                    {archivo.nombre}
                  </p>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500 dark:text-gray-400">
                    <span>{archivo.tamaño_formateado}</span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {archivo.fecha_modificacion}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleDescargar(archivo.nombre)}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-500 text-white rounded-xl text-sm font-medium hover:bg-orange-600 transition-colors"
                  >
                    <Download className="w-4 h-4" />
                    Descargar
                  </button>
                  <button
                    onClick={() => handleEliminar(archivo.nombre)}
                    disabled={eliminando === archivo.nombre}
                    className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                  >
                    {eliminando === archivo.nombre ? (
                      <RefreshCw className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
