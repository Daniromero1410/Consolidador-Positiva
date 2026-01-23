import axios from 'axios';
import { API_BASE } from '@/config/api';

const API_BASE_URL = API_BASE;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================
// MAESTRA
// ============================================

export const uploadMaestra = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/upload/maestra', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getMaestraResumen = async () => {
  const response = await api.get('/maestra/resumen');
  return response.data;
};

export const getMaestraEstado = async () => {
  const response = await api.get('/maestra/estado');
  return response.data;
};

export const getMaestraAnos = async () => {
  const response = await api.get('/maestra/años');
  return response.data;
};

export const getMaestraContratos = async (año?: number, numero?: string) => {
  const params = new URLSearchParams();
  if (año) params.append('año', año.toString());
  if (numero) params.append('numero', numero);
  
  const response = await api.get(`/maestra/contratos?${params}`);
  return response.data;
};

export const deleteMaestra = async () => {
  const response = await api.delete('/maestra');
  return response.data;
};

// ============================================
// SFTP
// ============================================

export const conectarSFTP = async () => {
  const response = await api.get('/sftp/conectar');
  return response.data;
};

export const desconectarSFTP = async () => {
  const response = await api.get('/sftp/desconectar');
  return response.data;
};

export const estadoSFTP = async () => {
  const response = await api.get('/sftp/estado');
  return response.data;
};

export const buscarContrato = async (numero: string, año: string) => {
  const response = await api.get(`/sftp/buscar-contrato?numero=${numero}&año=${año}`);
  return response.data;
};

// ============================================
// PROCESAMIENTO
// ============================================

export interface ProcesarRequest {
  año?: number;
  numero_contrato?: string;
  procesar_todo?: boolean;
}

export const iniciarProcesamiento = async (data: ProcesarRequest) => {
  const response = await api.post('/procesar', data);
  return response.data;
};

export const getEstadoJob = async (jobId: string) => {
  const response = await api.get(`/procesar/estado/${jobId}`);
  return response.data;
};

export const getLogsJob = async (jobId: string, desde: number = 0) => {
  const response = await api.get(`/procesar/logs/${jobId}?desde=${desde}`);
  return response.data;
};

export const cancelarJob = async (jobId: string) => {
  const response = await api.delete(`/procesar/cancelar/${jobId}`);
  return response.data;
};

export const getHistorial = async () => {
  const response = await api.get('/procesar/historial');
  return response.data;
};

export const getArchivosJob = async (jobId: string) => {
  const response = await api.get(`/procesar/job/${jobId}/archivos`);
  return response.data;
};

// ============================================
// DESCARGAS
// ============================================

export const listarArchivos = async () => {
  const response = await api.get('/descargas/listar');
  return response.data;
};

export const descargarArchivo = (filename: string) => {
  return `${API_BASE_URL}/descargas/archivo/${filename}`;
};

export const eliminarArchivo = async (filename: string) => {
  const response = await api.delete(`/descargas/archivo/${filename}`);
  return response.data;
};

export const limpiarArchivos = async () => {
  const response = await api.delete('/descargas/limpiar');
  return response.data;
};

export default api;
