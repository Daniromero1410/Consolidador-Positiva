"""
Cliente SFTP para GoAnywhere
============================

Módulo para conectarse al servidor SFTP de POSITIVA y navegar
la estructura de carpetas de contratos.
"""

import paramiko
import stat
import time
import os
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

from app.config import CONFIG


class TipoArchivo(Enum):
    CARPETA = "carpeta"
    ARCHIVO = "archivo"


@dataclass
class ItemSFTP:
    """Representa un archivo o carpeta en el SFTP."""
    nombre: str
    tipo: TipoArchivo
    tamaño: int = 0
    fecha_modificacion: str = ""
    ruta_completa: str = ""


class SFTPClientService:
    """Cliente SFTP para conectarse al GoAnywhere de POSITIVA."""
    
    def __init__(self):
        self.config = CONFIG
        self._client: Optional[paramiko.SSHClient] = None
        self._sftp: Optional[paramiko.SFTPClient] = None
        self._transport: Optional[paramiko.Transport] = None
        self._reconexiones = 0
        self._current_path = "/"
        self._conectado = False
    
    def _cerrar(self):
        """Cierra todas las conexiones."""
        for c in [self._sftp, self._client]:
            try:
                if c:
                    c.close()
            except:
                pass
        try:
            if self._transport:
                self._transport.close()
        except:
            pass
        self._sftp = self._client = self._transport = None
        self._conectado = False
    
    def conectar(self) -> bool:
        """
        Establece conexión con el servidor SFTP.
        
        Returns:
            True si la conexión fue exitosa
        """
        self._cerrar()
        
        for intento in range(self.config.MAX_REINTENTOS_CONEXION):
            try:
                self._client = paramiko.SSHClient()
                self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                self._client.connect(
                    hostname=self.config.HOST,
                    port=self.config.PORT,
                    username=self.config.USERNAME,
                    password=self.config.PASSWORD,
                    timeout=self.config.TIMEOUT_CONEXION,
                    banner_timeout=30,
                    auth_timeout=30,
                    allow_agent=False,
                    look_for_keys=False
                )
                
                self._transport = self._client.get_transport()
                if self._transport:
                    self._transport.set_keepalive(self.config.KEEPALIVE_INTERVAL)
                
                self._sftp = self._client.open_sftp()
                self._sftp.get_channel().settimeout(self.config.TIMEOUT_OPERACION)
                
                self._conectado = True
                self._reconexiones += 1
                
                return True
                
            except Exception as e:
                print(f"Intento {intento + 1} fallido: {e}")
                wait_time = self.config.BACKOFF_BASE ** intento
                time.sleep(wait_time)
        
        return False
    
    def desconectar(self):
        """Cierra la conexión SFTP."""
        self._cerrar()
    
    def esta_conectado(self) -> bool:
        """Verifica si hay una conexión activa."""
        if not self._conectado or not self._sftp:
            return False
        
        try:
            self._sftp.getcwd()
            return True
        except:
            self._conectado = False
            return False
    
    def reconectar_si_necesario(self) -> bool:
        """Reconecta si la conexión se perdió."""
        if not self.esta_conectado():
            return self.conectar()
        return True
    
    def listar_directorio(self, ruta: str = ".") -> List[ItemSFTP]:
        """
        Lista el contenido de un directorio.
        
        Args:
            ruta: Ruta del directorio a listar
            
        Returns:
            Lista de ItemSFTP con archivos y carpetas
        """
        if not self.reconectar_si_necesario():
            raise ConnectionError("No se pudo conectar al SFTP")
        
        items = []
        
        try:
            for entry in self._sftp.listdir_attr(ruta):
                nombre = entry.filename
                
                # Ignorar archivos ocultos
                if nombre.startswith('.'):
                    continue
                
                # Determinar tipo
                if stat.S_ISDIR(entry.st_mode):
                    tipo = TipoArchivo.CARPETA
                else:
                    tipo = TipoArchivo.ARCHIVO
                
                # Formatear fecha
                fecha = time.strftime('%Y-%m-%d %H:%M', time.localtime(entry.st_mtime))
                
                # Construir ruta completa
                if ruta == "." or ruta == "/":
                    ruta_completa = nombre
                else:
                    ruta_completa = f"{ruta.rstrip('/')}/{nombre}"
                
                items.append(ItemSFTP(
                    nombre=nombre,
                    tipo=tipo,
                    tamaño=entry.st_size,
                    fecha_modificacion=fecha,
                    ruta_completa=ruta_completa
                ))
            
            # Ordenar: carpetas primero, luego archivos
            items.sort(key=lambda x: (x.tipo.value, x.nombre.lower()))
            
        except Exception as e:
            raise Exception(f"Error al listar directorio {ruta}: {str(e)}")
        
        return items
    
    def navegar_a_carpeta_principal(self) -> bool:
        """
        Navega a la carpeta principal de contratos.
        
        Returns:
            True si se navegó exitosamente
        """
        if not self.reconectar_si_necesario():
            return False
        
        try:
            self._sftp.chdir(self.config.CARPETA_PRINCIPAL)
            self._current_path = self.config.CARPETA_PRINCIPAL
            return True
        except:
            return False
    
    def buscar_carpeta_contrato(self, numero_contrato: str, año: str) -> Optional[str]:
        """
        Busca la carpeta de un contrato específico.
        
        Args:
            numero_contrato: Número del contrato (ej: "45", "123")
            año: Año del contrato (ej: "2024")
            
        Returns:
            Nombre de la carpeta encontrada o None
        """
        if not self.reconectar_si_necesario():
            return None
        
        try:
            # Navegar a carpeta principal
            self._sftp.chdir(self.config.CARPETA_PRINCIPAL)
            
            # Listar carpetas
            items = self._sftp.listdir()
            
            # Patrones de búsqueda
            numero_limpio = str(int(numero_contrato)) if numero_contrato.isdigit() else numero_contrato
            numero_con_ceros = numero_limpio.zfill(3)
            numero_con_ceros_4 = numero_limpio.zfill(4)
            
            patrones = [
                f"{numero_limpio}-{año}",
                f"{numero_con_ceros}-{año}",
                f"{numero_con_ceros_4}-{año}",
                f"0{numero_limpio}-{año}",
            ]
            
            for carpeta in items:
                carpeta_upper = carpeta.upper()
                for patron in patrones:
                    if patron.upper() in carpeta_upper:
                        return carpeta
            
            return None
            
        except Exception as e:
            print(f"Error buscando contrato: {e}")
            return None
    
    def listar_carpeta_contrato(self, nombre_carpeta: str) -> Dict[str, Any]:
        """
        Lista el contenido de una carpeta de contrato.
        
        Args:
            nombre_carpeta: Nombre de la carpeta del contrato
            
        Returns:
            Diccionario con la estructura del contrato
        """
        if not self.reconectar_si_necesario():
            raise ConnectionError("No se pudo conectar al SFTP")
        
        resultado = {
            "nombre": nombre_carpeta,
            "ruta": f"{self.config.CARPETA_PRINCIPAL}/{nombre_carpeta}",
            "carpetas": [],
            "archivos": []
        }
        
        try:
            ruta = f"{self.config.CARPETA_PRINCIPAL}/{nombre_carpeta}"
            items = self.listar_directorio(ruta)
            
            for item in items:
                if item.tipo == TipoArchivo.CARPETA:
                    resultado["carpetas"].append({
                        "nombre": item.nombre,
                        "ruta": item.ruta_completa
                    })
                else:
                    resultado["archivos"].append({
                        "nombre": item.nombre,
                        "tamaño": item.tamaño,
                        "fecha": item.fecha_modificacion,
                        "ruta": item.ruta_completa
                    })
            
        except Exception as e:
            raise Exception(f"Error al listar carpeta {nombre_carpeta}: {str(e)}")
        
        return resultado
    
    def descargar_archivo(self, ruta_remota: str, ruta_local: str) -> bool:
        """
        Descarga un archivo del servidor SFTP.
        
        Args:
            ruta_remota: Ruta del archivo en el servidor
            ruta_local: Ruta donde guardar el archivo localmente
            
        Returns:
            True si se descargó exitosamente
        """
        if not self.reconectar_si_necesario():
            raise ConnectionError("No se pudo conectar al SFTP")
        
        try:
            # Crear carpeta local si no existe
            os.makedirs(os.path.dirname(ruta_local), exist_ok=True)
            
            # Descargar archivo
            self._sftp.get(ruta_remota, ruta_local)
            
            return True
            
        except Exception as e:
            raise Exception(f"Error al descargar {ruta_remota}: {str(e)}")
    
    def obtener_info_archivo(self, ruta: str) -> Dict[str, Any]:
        """
        Obtiene información detallada de un archivo.
        
        Args:
            ruta: Ruta del archivo
            
        Returns:
            Diccionario con información del archivo
        """
        if not self.reconectar_si_necesario():
            raise ConnectionError("No se pudo conectar al SFTP")
        
        try:
            attr = self._sftp.stat(ruta)
            
            return {
                "nombre": os.path.basename(ruta),
                "ruta": ruta,
                "tamaño": attr.st_size,
                "fecha_modificacion": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(attr.st_mtime)),
                "es_carpeta": stat.S_ISDIR(attr.st_mode)
            }
            
        except Exception as e:
            raise Exception(f"Error al obtener info de {ruta}: {str(e)}")
    
    def obtener_estructura_completa(self, ruta_base: str, profundidad: int = 2) -> Dict[str, Any]:
        """
        Obtiene la estructura completa de carpetas de forma recursiva.
        
        Args:
            ruta_base: Ruta base desde donde empezar
            profundidad: Niveles de profundidad a explorar
            
        Returns:
            Estructura jerárquica de carpetas y archivos
        """
        if not self.reconectar_si_necesario():
            raise ConnectionError("No se pudo conectar al SFTP")
        
        if profundidad <= 0:
            return {"nombre": ruta_base.split("/")[-1], "tipo": "carpeta", "hijos": []}
        
        resultado = {
            "nombre": ruta_base.split("/")[-1] or ruta_base,
            "ruta": ruta_base,
            "tipo": "carpeta",
            "hijos": []
        }
        
        try:
            items = self.listar_directorio(ruta_base)
            
            for item in items:
                if item.tipo == TipoArchivo.CARPETA:
                    # Recursión para subcarpetas
                    sub_estructura = self.obtener_estructura_completa(
                        item.ruta_completa, 
                        profundidad - 1
                    )
                    resultado["hijos"].append(sub_estructura)
                else:
                    resultado["hijos"].append({
                        "nombre": item.nombre,
                        "ruta": item.ruta_completa,
                        "tipo": "archivo",
                        "tamaño": item.tamaño,
                        "fecha": item.fecha_modificacion
                    })
                    
        except Exception as e:
            resultado["error"] = str(e)
        
        return resultado


# Instancia global del cliente SFTP
sftp_client = SFTPClientService()
