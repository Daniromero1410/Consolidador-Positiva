// ============================================
// MAESTRA
// ============================================

export interface ContratoInfo {
  numero: string;
  razon_social: string;
  codigo_completo: string;
}

export interface ContratosAno {
  cantidad: number;
  contratos: ContratoInfo[];
}

export interface MaestraResumen {
  años_disponibles: number[];
  contratos_por_año: Record<string, ContratosAno>;
  total_contratos: number;
  hoja_utilizada: string;
  total_registros_maestra: number;
  total_prestadores: number;
}

export interface MaestraEstado {
  cargada: boolean;
  archivo: string | null;
  total_registros?: number;
  total_prestadores?: number;
  años_disponibles?: number[];
  total_contratos?: number;
  mensaje?: string;
  error?: string;
}

export interface AnoInfo {
  año: number;
  cantidad_contratos: number;
}

// ============================================
// SFTP
// ============================================

export interface SFTPEstado {
  conectado: boolean;
  servidor: string | null;
}

export interface ItemSFTP {
  nombre: string;
  tipo: 'carpeta' | 'archivo';
  tamaño: number;
  fecha: string;
  ruta: string;
}

// ============================================
// PROCESAMIENTO
// ============================================

export interface LogEntry {
  timestamp: string;
  tipo: 'info' | 'success' | 'warning' | 'error' | 'file' | 'download' | 'process' | 'contract';
  mensaje: string;
}

export interface JobEstado {
  job_id: string;
  estado: 'pendiente' | 'en_proceso' | 'completado' | 'error' | 'cancelado';
  progreso: number;
  mensaje: string;
  modo: string;
  año: string | null;
  numero_contrato: string | null;
  contratos_total: number;
  contratos_procesados: number;
  contrato_actual: string;
  inicio: string;
  fin: string | null;
  archivos_generados: string[];
  errores: string[];
  estadisticas: Record<string, number>;
  total_logs?: number;
}

export interface JobLogs {
  success: boolean;
  job_id: string;
  estado: string;
  progreso: number;
  mensaje: string;
  contrato_actual: string;
  total_logs: number;
  logs: LogEntry[];
  archivos_generados: string[];
}

export interface JobHistorial {
  job_id: string;
  estado: string;
  modo: string;
  año: string | null;
  contratos_total: number;
  contratos_procesados: number;
  inicio: string;
  fin: string | null;
  archivos_generados: number;
}

// ============================================
// DESCARGAS
// ============================================

export interface ArchivoDescarga {
  nombre: string;
  tamaño: number;
  tamaño_formateado: string;
  fecha_modificacion: number;
  ruta: string;
}
