'use client';

import { useState, useCallback, useEffect, useMemo, createContext, useContext } from 'react';
import {
  Upload,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  Trash2,
  RefreshCw,
  Calendar,
  AlertCircle,
  File,
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  ArrowUpDown,
  Building2,
  Hash
} from 'lucide-react';
import { API_BASE } from '@/config/api';

// Hook para obtener el tema del localStorage
function useTheme() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  
  useEffect(() => {
    const checkTheme = () => {
      const saved = localStorage.getItem('theme');
      setTheme(saved === 'dark' ? 'dark' : 'light');
    };
    
    checkTheme();
    
    // Escuchar cambios en el storage
    window.addEventListener('storage', checkTheme);
    
    // También verificar periódicamente (para cambios en la misma pestaña)
    const interval = setInterval(checkTheme, 100);
    
    return () => {
      window.removeEventListener('storage', checkTheme);
      clearInterval(interval);
    };
  }, []);
  
  return theme;
}

interface Contrato {
  numero: string;
  año: number;
  razon_social: string;
  nit?: string;
  departamento?: string;
  municipio?: string;
}

interface MaestraEstado {
  cargada: boolean;
  archivo: string | null;
  total_contratos?: number;
  total_prestadores?: number;
  años_disponibles?: number[];
}

export default function MaestraPage() {
  const theme = useTheme();
  const isDark = theme === 'dark';
  
  // Estado de la maestra
  const [estado, setEstado] = useState<MaestraEstado | null>(null);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Estado de la tabla
  const [contratos, setContratos] = useState<Contrato[]>([]);
  const [loadingContratos, setLoadingContratos] = useState(false);
  
  // Filtros
  const [busqueda, setBusqueda] = useState('');
  const [filtroAño, setFiltroAño] = useState<string>('todos');
  
  // Paginación
  const [pagina, setPagina] = useState(1);
  const [porPagina, setPorPagina] = useState(10);
  
  // Ordenamiento
  const [ordenCampo, setOrdenCampo] = useState<keyof Contrato>('numero');
  const [ordenDir, setOrdenDir] = useState<'asc' | 'desc'>('asc');

  // Estilos basados en tema
  const styles = {
    card: {
      backgroundColor: isDark ? '#1f2937' : '#ffffff',
      borderColor: isDark ? '#374151' : '#e5e7eb',
    },
    cardHover: {
      backgroundColor: isDark ? '#374151' : '#f9fafb',
    },
    text: {
      primary: isDark ? '#ffffff' : '#111827',
      secondary: isDark ? '#9ca3af' : '#6b7280',
      muted: isDark ? '#6b7280' : '#9ca3af',
    },
    input: {
      backgroundColor: isDark ? '#374151' : '#f9fafb',
      borderColor: isDark ? '#4b5563' : '#e5e7eb',
      color: isDark ? '#ffffff' : '#111827',
    },
    table: {
      headerBg: isDark ? 'rgba(55, 65, 81, 0.5)' : '#f9fafb',
      rowHover: isDark ? 'rgba(55, 65, 81, 0.5)' : '#f9fafb',
      border: isDark ? '#374151' : '#f3f4f6',
    }
  };

  // Cargar estado inicial
  const cargarEstado = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/maestra/estado`);
      const data = await res.json();
      setEstado(data);
      
      if (data.cargada) {
        cargarContratos();
      }
    } catch (err) {
      console.error('Error cargando estado:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Cargar contratos
  const cargarContratos = async () => {
    setLoadingContratos(true);
    try {
      const res = await fetch(`${API_BASE}/maestra/contratos/todos`);
      const data = await res.json();
      if (data.contratos) {
        setContratos(data.contratos);
      }
    } catch (err) {
      console.error('Error cargando contratos:', err);
    } finally {
      setLoadingContratos(false);
    }
  };

  useEffect(() => {
    cargarEstado();
  }, [cargarEstado]);

  // Auto-limpiar mensajes
  useEffect(() => {
    if (error || success) {
      const timer = setTimeout(() => {
        setError(null);
        setSuccess(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [error, success]);

  // Filtrar y ordenar contratos
  const contratosFiltrados = useMemo(() => {
    let resultado = [...contratos];
    
    if (busqueda) {
      const busquedaLower = busqueda.toLowerCase();
      resultado = resultado.filter(c => 
        c.numero?.toLowerCase().includes(busquedaLower) ||
        c.razon_social?.toLowerCase().includes(busquedaLower) ||
        c.nit?.toLowerCase().includes(busquedaLower) ||
        c.departamento?.toLowerCase().includes(busquedaLower) ||
        c.municipio?.toLowerCase().includes(busquedaLower)
      );
    }
    
    if (filtroAño !== 'todos') {
      resultado = resultado.filter(c => c.año === parseInt(filtroAño));
    }
    
    resultado.sort((a, b) => {
      const valorA = a[ordenCampo] || '';
      const valorB = b[ordenCampo] || '';
      
      if (typeof valorA === 'number' && typeof valorB === 'number') {
        return ordenDir === 'asc' ? valorA - valorB : valorB - valorA;
      }
      
      const strA = String(valorA).toLowerCase();
      const strB = String(valorB).toLowerCase();
      
      return ordenDir === 'asc' ? strA.localeCompare(strB) : strB.localeCompare(strA);
    });
    
    return resultado;
  }, [contratos, busqueda, filtroAño, ordenCampo, ordenDir]);

  // Paginación
  const totalPaginas = Math.ceil(contratosFiltrados.length / porPagina);
  const contratosPaginados = contratosFiltrados.slice(
    (pagina - 1) * porPagina,
    pagina * porPagina
  );

  useEffect(() => {
    setPagina(1);
  }, [busqueda, filtroAño]);

  const handleOrdenar = (campo: keyof Contrato) => {
    if (ordenCampo === campo) {
      setOrdenDir(ordenDir === 'asc' ? 'desc' : 'asc');
    } else {
      setOrdenCampo(campo);
      setOrdenDir('asc');
    }
  };

  const handleFile = async (file: File) => {
    setError(null);
    setSuccess(null);
    
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['xlsx', 'xls', 'xlsb', 'xlsm'].includes(ext || '')) {
      setError('Formato no soportado. Use .xlsx, .xls, .xlsb o .xlsm');
      return;
    }

    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await fetch(`${API_BASE}/upload/maestra`, {
        method: 'POST',
        body: formData
      });
      
      const data = await res.json();
      
      if (res.ok && data.success) {
        setSuccess(data.mensaje || 'Maestra cargada exitosamente');
        await cargarEstado();
      } else {
        setError(data.detail || 'Error al cargar');
      }
    } catch (err: any) {
      setError(err.message || 'Error al cargar el archivo');
    } finally {
      setUploading(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const handleEliminar = async () => {
    if (!confirm('¿Está seguro de eliminar la maestra actual?')) return;
    
    try {
      const res = await fetch(`${API_BASE}/maestra`, { method: 'DELETE' });
      if (res.ok) {
        setEstado({ cargada: false, archivo: null });
        setContratos([]);
        setSuccess('Maestra eliminada correctamente');
      }
    } catch (err) {
      setError('Error al eliminar');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <RefreshCw className="w-8 h-8 animate-spin" style={{ color: '#f97316' }} />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold" style={{ color: styles.text.primary }}>Cargar Maestra</h1>
        <p style={{ color: styles.text.secondary }} className="mt-1">
          Gestione el archivo de maestra de contratos vigentes
        </p>
      </div>

      {/* Alertas */}
      {error && (
        <div 
          className="p-4 rounded-xl flex items-center gap-3"
          style={{ 
            backgroundColor: isDark ? 'rgba(239, 68, 68, 0.1)' : '#fef2f2',
            border: `1px solid ${isDark ? 'rgba(239, 68, 68, 0.2)' : '#fecaca'}`
          }}
        >
          <XCircle className="w-5 h-5 flex-shrink-0" style={{ color: '#ef4444' }} />
          <p className="text-sm" style={{ color: isDark ? '#fca5a5' : '#b91c1c' }}>{error}</p>
          <button onClick={() => setError(null)} className="ml-auto" style={{ color: '#f87171' }}>
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}
      
      {success && (
        <div 
          className="p-4 rounded-xl flex items-center gap-3"
          style={{ 
            backgroundColor: isDark ? 'rgba(34, 197, 94, 0.1)' : '#f0fdf4',
            border: `1px solid ${isDark ? 'rgba(34, 197, 94, 0.2)' : '#bbf7d0'}`
          }}
        >
          <CheckCircle className="w-5 h-5 flex-shrink-0" style={{ color: '#22c55e' }} />
          <p className="text-sm" style={{ color: isDark ? '#86efac' : '#166534' }}>{success}</p>
          <button onClick={() => setSuccess(null)} className="ml-auto" style={{ color: '#4ade80' }}>
            <XCircle className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Maestra actual - Banner */}
      {estado?.cargada && (
        <div 
          className="rounded-2xl p-6 text-white"
          style={{ background: 'linear-gradient(135deg, #f97316, #ea580c)' }}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium" style={{ color: 'rgba(255,255,255,0.8)' }}>Maestra Activa</p>
              <h2 className="text-xl font-bold mt-1">{estado.archivo}</h2>
              <div className="flex items-center gap-4 mt-3">
                <div className="flex items-center gap-2">
                  <FileSpreadsheet className="w-4 h-4" style={{ color: 'rgba(255,255,255,0.7)' }} />
                  <span className="text-sm">{estado.total_contratos?.toLocaleString()} contratos</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4" style={{ color: 'rgba(255,255,255,0.7)' }} />
                  <span className="text-sm">{estado.años_disponibles?.length} años</span>
                </div>
              </div>
            </div>
            <button
              onClick={handleEliminar}
              className="p-3 rounded-xl transition-colors"
              style={{ backgroundColor: 'rgba(255,255,255,0.2)' }}
              title="Eliminar maestra"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}

      {/* Zona de carga */}
      {!estado?.cargada && (
        <div 
          className="rounded-2xl p-6"
          style={{ ...styles.card, border: `1px solid ${styles.card.borderColor}` }}
        >
          <h2 className="text-lg font-semibold mb-4" style={{ color: styles.text.primary }}>
            Subir Archivo
          </h2>
          
          <div
            onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
            onDragLeave={() => setDragActive(false)}
            onDrop={handleDrop}
            className="relative rounded-2xl p-10 text-center transition-all cursor-pointer"
            style={{ 
              border: `2px dashed ${dragActive ? '#f97316' : styles.card.borderColor}`,
              backgroundColor: dragActive ? (isDark ? 'rgba(249, 115, 22, 0.1)' : '#fff7ed') : 'transparent',
              opacity: uploading ? 0.5 : 1,
              pointerEvents: uploading ? 'none' : 'auto'
            }}
          >
            <input
              type="file"
              accept=".xlsx,.xls,.xlsb,.xlsm"
              onChange={handleChange}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              disabled={uploading}
            />
            
            <div className="flex flex-col items-center">
              {uploading ? (
                <RefreshCw className="w-12 h-12 animate-spin mb-4" style={{ color: '#f97316' }} />
              ) : (
                <div 
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4"
                  style={{ backgroundColor: isDark ? 'rgba(249, 115, 22, 0.2)' : '#ffedd5' }}
                >
                  <Upload className="w-8 h-8" style={{ color: '#f97316' }} />
                </div>
              )}
              
              <p className="font-medium mb-1" style={{ color: styles.text.primary }}>
                {uploading ? 'Procesando archivo...' : 'Arrastra tu archivo aquí'}
              </p>
              <p className="text-sm mb-4" style={{ color: styles.text.secondary }}>
                o haz clic para seleccionar
              </p>
              
              <span 
                className="px-4 py-2 rounded-xl text-sm font-medium text-white"
                style={{ backgroundColor: '#f97316' }}
              >
                Seleccionar archivo
              </span>
              
              <p className="text-xs mt-4" style={{ color: styles.text.muted }}>
                Formatos: .xlsx, .xls, .xlsb, .xlsm
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Tabla de contratos */}
      {estado?.cargada && (
        <div 
          className="rounded-2xl overflow-hidden"
          style={{ ...styles.card, border: `1px solid ${styles.card.borderColor}` }}
        >
          {/* Header de tabla con filtros */}
          <div 
            className="p-4"
            style={{ borderBottom: `1px solid ${styles.card.borderColor}` }}
          >
            <div className="flex flex-col lg:flex-row lg:items-center gap-4">
              <div>
                <h2 className="text-lg font-semibold" style={{ color: styles.text.primary }}>Contratos</h2>
                <p className="text-sm" style={{ color: styles.text.secondary }}>
                  {contratosFiltrados.length} de {contratos.length} contratos
                </p>
              </div>
              
              <div className="flex flex-1 flex-col sm:flex-row gap-3 lg:justify-end">
                {/* Búsqueda */}
                <div className="relative flex-1 max-w-md">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: styles.text.muted }} />
                  <input
                    type="text"
                    value={busqueda}
                    onChange={(e) => setBusqueda(e.target.value)}
                    placeholder="Buscar por número, razón social, NIT..."
                    className="w-full pl-10 pr-4 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                    style={styles.input}
                  />
                </div>
                
                {/* Filtro por año */}
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4" style={{ color: styles.text.muted }} />
                  <select
                    value={filtroAño}
                    onChange={(e) => setFiltroAño(e.target.value)}
                    className="px-3 py-2 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
                    style={styles.input}
                  >
                    <option value="todos">Todos los años</option>
                    {estado.años_disponibles?.sort((a, b) => b - a).map(año => (
                      <option key={año} value={año}>{año}</option>
                    ))}
                  </select>
                </div>
                
                {/* Botón recargar */}
                <button
                  onClick={cargarContratos}
                  disabled={loadingContratos}
                  className="p-2 rounded-xl disabled:opacity-50"
                  style={{ backgroundColor: styles.input.backgroundColor }}
                >
                  <RefreshCw 
                    className={`w-4 h-4 ${loadingContratos ? 'animate-spin' : ''}`} 
                    style={{ color: styles.text.secondary }} 
                  />
                </button>
              </div>
            </div>
          </div>
          
          {/* Tabla */}
          <div className="overflow-x-auto">
            {loadingContratos ? (
              <div className="flex items-center justify-center py-12">
                <RefreshCw className="w-8 h-8 animate-spin" style={{ color: '#f97316' }} />
              </div>
            ) : contratosFiltrados.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12" style={{ color: styles.text.muted }}>
                <File className="w-12 h-12 mb-3 opacity-30" />
                <p>No se encontraron contratos</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full min-w-[800px]">
                  <thead>
                    <tr style={{ backgroundColor: styles.table.headerBg }}>
                      <th className="px-3 py-3 text-left w-24">
                        <button
                          onClick={() => handleOrdenar('numero')}
                          className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider"
                          style={{ color: styles.text.muted }}
                        >
                          <Hash className="w-3 h-3" />
                          Contrato
                          <ArrowUpDown className="w-3 h-3" />
                        </button>
                      </th>
                      <th className="px-3 py-3 text-left w-20">
                        <button
                          onClick={() => handleOrdenar('año')}
                          className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider"
                          style={{ color: styles.text.muted }}
                        >
                          <Calendar className="w-3 h-3" />
                          Año
                          <ArrowUpDown className="w-3 h-3" />
                        </button>
                      </th>
                      <th className="px-3 py-3 text-left w-32">
                        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: styles.text.muted }}>
                          NIT
                        </span>
                      </th>
                      <th className="px-3 py-3 text-left">
                        <button
                          onClick={() => handleOrdenar('razon_social')}
                          className="flex items-center gap-1 text-xs font-semibold uppercase tracking-wider"
                          style={{ color: styles.text.muted }}
                        >
                          <Building2 className="w-3 h-3" />
                          Razón Social
                          <ArrowUpDown className="w-3 h-3" />
                        </button>
                      </th>
                      <th className="px-3 py-3 text-left w-36">
                        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: styles.text.muted }}>
                          Departamento
                        </span>
                      </th>
                      <th className="px-3 py-3 text-left w-36">
                        <span className="text-xs font-semibold uppercase tracking-wider" style={{ color: styles.text.muted }}>
                          Ciudad
                        </span>
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {contratosPaginados.map((contrato, idx) => (
                      <tr
                        key={`${contrato.numero}-${contrato.año}-${idx}`}
                        className="transition-colors"
                        style={{ borderBottom: `1px solid ${styles.table.border}` }}
                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = styles.table.rowHover}
                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                      >
                        <td className="px-3 py-3">
                          <span className="font-medium text-sm" style={{ color: styles.text.primary }}>
                            #{contrato.numero}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <span
                            className="px-2 py-1 rounded-lg text-xs font-medium whitespace-nowrap"
                            style={{
                              backgroundColor: isDark ? 'rgba(249, 115, 22, 0.2)' : '#ffedd5',
                              color: isDark ? '#fdba74' : '#c2410c'
                            }}
                          >
                            {contrato.año}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <span className="text-sm font-mono" style={{ color: styles.text.secondary }}>
                            {contrato.nit || '-'}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <span className="text-sm" style={{ color: isDark ? '#d1d5db' : '#374151' }}>
                            {contrato.razon_social || '-'}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <span className="text-sm" style={{ color: styles.text.secondary }}>
                            {contrato.departamento || '-'}
                          </span>
                        </td>
                        <td className="px-3 py-3">
                          <span className="text-sm" style={{ color: styles.text.secondary }}>
                            {contrato.municipio || '-'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
          
          {/* Paginación */}
          {contratosFiltrados.length > 0 && (
            <div 
              className="px-4 py-3 flex flex-col sm:flex-row items-center justify-between gap-4"
              style={{ borderTop: `1px solid ${styles.card.borderColor}` }}
            >
              <div className="flex items-center gap-2 text-sm" style={{ color: styles.text.secondary }}>
                <span>Mostrando</span>
                <select
                  value={porPagina}
                  onChange={(e) => { setPorPagina(Number(e.target.value)); setPagina(1); }}
                  className="px-2 py-1 rounded-lg text-sm"
                  style={styles.input}
                >
                  <option value={10}>10</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <span>de {contratosFiltrados.length}</span>
              </div>
              
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setPagina(1)}
                  disabled={pagina === 1}
                  className="p-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ color: styles.text.secondary }}
                >
                  <ChevronsLeft className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPagina(p => Math.max(1, p - 1))}
                  disabled={pagina === 1}
                  className="p-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ color: styles.text.secondary }}
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                
                <div className="flex items-center gap-1 mx-2">
                  {Array.from({ length: Math.min(5, totalPaginas) }, (_, i) => {
                    let pageNum;
                    if (totalPaginas <= 5) {
                      pageNum = i + 1;
                    } else if (pagina <= 3) {
                      pageNum = i + 1;
                    } else if (pagina >= totalPaginas - 2) {
                      pageNum = totalPaginas - 4 + i;
                    } else {
                      pageNum = pagina - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setPagina(pageNum)}
                        className="w-8 h-8 rounded-lg text-sm font-medium transition-colors"
                        style={{ 
                          backgroundColor: pagina === pageNum ? '#f97316' : 'transparent',
                          color: pagina === pageNum ? '#ffffff' : styles.text.secondary
                        }}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                </div>
                
                <button
                  onClick={() => setPagina(p => Math.min(totalPaginas, p + 1))}
                  disabled={pagina === totalPaginas}
                  className="p-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ color: styles.text.secondary }}
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setPagina(totalPaginas)}
                  disabled={pagina === totalPaginas}
                  className="p-2 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ color: styles.text.secondary }}
                >
                  <ChevronsRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
