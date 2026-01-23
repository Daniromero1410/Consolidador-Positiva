/**
 * Configuración centralizada de la API
 *
 * Esta configuración permite que la aplicación funcione desde cualquier dispositivo.
 * La URL de la API se obtiene de las variables de entorno.
 *
 * Para cambiar la URL:
 * 1. Edita el archivo .env.local en la raíz del frontend
 * 2. Cambia NEXT_PUBLIC_API_URL a la IP/dominio de tu servidor
 * 3. Reinicia el servidor de desarrollo
 */

export const API_CONFIG = {
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
} as const;

export const getApiUrl = (endpoint: string): string => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// Exportar también como constante para compatibilidad
export const API_BASE = API_CONFIG.BASE_URL;
