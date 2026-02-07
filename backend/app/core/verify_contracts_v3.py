
import os
import re
import sys
import paramiko
import stat
import time
import pandas as pd
import shutil
import warnings
from typing import List, Optional, Dict, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

# ==========================================
# CONFIGURACION Y LOGGING ORIGINAL
# ==========================================

@dataclass
class Config:
    """Configuración centralizada del sistema."""
    HOST: str = 'mft.positiva.gov.co'
    PORT: int = 2243
    USERNAME: str = 'G_medica'
    PASSWORD: str = 'Uhnbru0sgnpit]'
    TIMEOUT_CONEXION: int = 30
    TIMEOUT_OPERACION: int = 20
    TIMEOUT_ARCHIVO: int = 60
    MAX_REINTENTOS_CONEXION: int = 5
    MAX_REINTENTOS_OPERACION: int = 3
    BACKOFF_BASE: float = 2.0
    KEEPALIVE_INTERVAL: int = 5
    CARPETA_PRINCIPAL: str = 'R.A-ABASTECIMIENTO RED ASISTENCIAL'
    CARPETA_TRABAJO: str = './trabajo_temp_test'
    CONTRATOS_PROBLEMATICOS: set = field(default_factory=lambda: {'572-2023'})
    TIMEOUT_CONTRATOS_PROBLEMATICOS: int = 30
    MAX_SEDES: int = 50

CONFIG = Config()

class LogLevel(Enum):
    INFO = "ℹ️"
    SUCCESS = "✅"
    WARNING = "⚠️"
    ERROR = "❌"
    DEBUG = "🐛"
    NAV = "📂"
    FILE = "📄"
    DOWNLOAD = "⬇️"
    PROCESS = "⚙️"
    ALERT = "🔔"

class Logger:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.indent_level = 0
    
    def _print(self, level, msg):
        print(f"{'  ' * self.indent_level}{level.value} {msg}")

    def info(self, msg, detail=""): self._print(LogLevel.INFO, f"{msg} {detail}")
    def success(self, msg, detail=""): self._print(LogLevel.SUCCESS, f"{msg} {detail}")
    def warning(self, msg, detail=""): self._print(LogLevel.WARNING, f"{msg} {detail}")
    def error(self, msg, detail=""): self._print(LogLevel.ERROR, f"{msg} {detail}")
    def debug(self, msg, detail=""): 
        if self.verbose: self._print(LogLevel.DEBUG, f"{msg} {detail}")
    def nav(self, path): self._print(LogLevel.NAV, path)
    def download(self, path): self._print(LogLevel.DOWNLOAD, path)
    def indent(self): self.indent_level += 1
    def dedent(self): self.indent_level = max(0, self.indent_level - 1)
    def file_found(self, name, type=""): self._print(LogLevel.FILE, f"{name} ({type})")
    def alert(self, type, msg, file=""): self._print(LogLevel.ALERT, f"[{type}] {msg} ({file})")

    def header(self, msg):
        print(f"\n{'='*60}\n  {msg}\n{'='*60}")

LOG = Logger(verbose=True)

# ==========================================
# CLIENTE SFTP
# ==========================================

class SFTPClient:
    def __init__(self, config: Config, logger: Logger):
        self.config = config
        self.log = logger
        self._client = None
        self._sftp = None
        self._transport = None
        self._current_path = "/"
        self._reconexiones = 0

    def conectar(self, silencioso: bool = False) -> bool:
        try:
            if not silencioso: self.log.info(f"Conectando a {self.config.HOST}...")
            self._client = paramiko.SSHClient()
            self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self._client.connect(
                hostname=self.config.HOST, port=self.config.PORT,
                username=self.config.USERNAME, password=self.config.PASSWORD,
                timeout=self.config.TIMEOUT_CONEXION, look_for_keys=False, allow_agent=False
            )
            self._transport = self._client.get_transport()
            self._transport.set_keepalive(self.config.KEEPALIVE_INTERVAL)
            self._sftp = self._client.open_sftp()
            if not silencioso: self.log.success("Conectado")
            return True
        except Exception as e:
            if not silencioso: self.log.error(f"Error conexión: {e}")
            return False

    def listar(self, ruta: str = '.') -> List[Dict]:
        try:
            return [{'nombre': a.filename, 'es_directorio': stat.S_ISDIR(a.st_mode), 'tamano': a.st_size} 
                    for a in self._sftp.listdir_attr(ruta)]
        except Exception as e:
            self.log.error(f"Error listar: {e}")
            return []

    def cd(self, ruta: str, log_nav: bool = True):
        try:
            self._sftp.chdir(ruta)
            self._current_path = self._sftp.getcwd() or ruta
            if log_nav: self.log.nav(self._current_path)
        except Exception as e:
            self.log.error(f"Error CD {ruta}: {e}")

    def descargar(self, remoto: str, local: str):
        try:
            self.log.download(remoto)
            self._sftp.get(remoto, local)
        except Exception as e:
            self.log.error(f"Error descargar {remoto}: {e}")

    def desconectar(self):
        if self._client: self._client.close()
    
    @property
    def reconexiones(self): return self._reconexiones

# ==========================================
# CONSTANTES Y VALIDACIONES (CORREGIDAS)
# ==========================================

CIUDADES_COLOMBIA_COMPLETA = {'BOGOTÁ', 'MEDELLÍN', 'CALI', 'BARRANQUILLA', 'BUCARAMANGA', 'CARTAGENA'} # Reducida para test
DEPARTAMENTOS_COLOMBIA = {'ANTIOQUIA', 'CUNDINAMARCA', 'VALLE'}
PALABRAS_INVALIDAS_CUPS = ['CODIGO', 'DESCRIPCION', 'TARIFA', 'TOTAL']
PREFIJOS_CELULAR_COLOMBIA = {'300', '301', '302', '310', '311', '315', '320', '321', '350', '351'}

def es_telefono_celular(valor: str) -> bool:
    if not valor: return False
    v = re.sub(r'[^\d]', '', str(valor))
    return len(v) == 10 and v[:3] in PREFIJOS_CELULAR_COLOMBIA

def validar_cups(cups: str, fila: list = None) -> bool:
    """VALIDACION CORREGIDA v2"""
    if not cups: return False
    cups_str = str(cups).strip().replace('\t', '')
    if cups_str.endswith('.0'): cups_str = cups_str[:-2]
    cups_u = cups_str.upper()

    if len(cups_str) > 25: return False
    if cups_u in CIUDADES_COLOMBIA_COMPLETA: return False
    
    for p in PALABRAS_INVALIDAS_CUPS:
        if p in cups_u: return False

    cups_digits = re.sub(r'[^\d]', '', cups_str)

    # CORRECCION 1: Monetario solo si es puramente numérico y muy largo
    if cups_digits and len(cups_digits) >= 10 and cups_digits == cups_str:
        # Podría ser monetario muy grande o habilitación
        pass
    elif cups_digits and len(cups_digits) >= 7 and cups_digits != cups_str:
         pass # Permitir alfanumericos largos (ej 123456-01)
    
    # CORRECCION 2: Rango Habilitación (10-12)
    if cups_digits and cups_digits == cups_str and 10 <= len(cups_digits) <= 12:
        return False # Posible habilitación

    if es_telefono_celular(cups_str): return False
    
    return True

def es_archivo_tarifas_valido(nombre: str) -> tuple:
    if not nombre: return False, 'INVALIDO'
    nombre_upper = nombre.upper().replace('\t', '').strip() # CORRECCION TABS
    
    if re.search(r'AN[AÁ]LISIS\s*(DE\s*)?(TARIFAS?|TARIFA)', nombre_upper): return False, 'INVALIDO'
    
    if 'ANEXO' in nombre_upper and ('TARIFA' in nombre_upper or 'SERV' in nombre_upper): # Generoso para test
         return True, 'ANEXO_TEST'
    
    patrones = [r'ANEXO\s*[_ \-]*0?1', r'TARIFAS']
    for p in patrones:
        if re.search(p, nombre_upper): return True, 'ANEXO_1'
        
    return False, 'INVALIDO'

# ==========================================
# BUSCADOR Y LOGICA DE NAVEGACION
# ==========================================

class BuscadorAnexos:
    def __init__(self, cliente, config, logger):
        self.cliente = cliente
        self.config = config
        self.log = logger
        self.alertas = []

    def buscar_carpeta(self, carpetas, texto):
        for c in carpetas:
            if texto.upper() in c.upper(): return c
        return None

    def buscar_carpeta_contrato(self, carpetas, numero):
        num = str(numero).lstrip('0')
        variantes = [num, '0'+num, num.zfill(4)]
        for v in variantes:
            for c in carpetas:
                if c.startswith(v+'-') or c.startswith(v+' ') or c.startswith(v+'_'):
                    return c
        return None

    def navegar_y_descargar(self, ano, numero, destino):
        self.log.info(f"Navegando a contrato {numero}-{ano}...")
        self.cliente.cd('/', log_nav=False)
        
        items = self.cliente.listar()
        carpetas = [i['nombre'] for i in items if i['es_directorio']]
        cp = self.buscar_carpeta(carpetas, self.config.CARPETA_PRINCIPAL)
        if not cp: return False, "No carpeta principal"
        self.cliente.cd(cp)

        items = self.cliente.listar()
        carpetas = [i['nombre'] for i in items if i['es_directorio']]
        ca = self.buscar_carpeta(carpetas, f'contratos {ano}')
        if not ca: return False, f"No carpeta ano {ano}"
        self.cliente.cd(ca)

        items = self.cliente.listar()
        carpetas = [i['nombre'] for i in items if i['es_directorio']]
        cc = self.buscar_carpeta_contrato(carpetas, numero)
        if not cc: 
             self.log.error(f"Contrato {numero} no encontrado en {ca}")
             return False, "Contrato no encontrado"
        
        self.cliente.cd(cc)
        self.log.success(f"En carpeta contrato: {cc}")

        # Buscar tarifas
        items = self.cliente.listar()
        carpetas = [i['nombre'] for i in items if i['es_directorio']]
        ct = self.buscar_carpeta(carpetas, 'tarifa')
        if not ct: return False, "No carpeta tarifas"
        
        self.cliente.cd(ct)
        items = self.cliente.listar()
        archivos = [i['nombre'] for i in items if not i['es_directorio']]
        
        descargados = []
        for arch in archivos:
            valido, tipo = es_archivo_tarifas_valido(arch)
            if valido:
                local = os.path.join(destino, arch)
                self.cliente.descargar(arch, local)
                descargados.append(local)
            else:
                self.log.warning(f"Archivo ignorado: {arch}")
                
        return True, descargados

# ==========================================
# MAIN TEST
# ==========================================

def test_contratos():
    os.makedirs(CONFIG.CARPETA_TRABAJO, exist_ok=True)
    cliente = SFTPClient(CONFIG, LOG)
    
    if not cliente.conectar():
        return

    buscador = BuscadorAnexos(cliente, CONFIG, LOG)
    
    # CONTRATOS A PROBAR
    contratos = [
        {'numero': '531', 'ano': '2024'},
        {'numero': '635', 'ano': '2024'}
    ]

    for c in contratos:
        LOG.header(f"TEST CONTRATO {c['numero']}-{c['ano']}")
        folder = os.path.join(CONFIG.CARPETA_TRABAJO, f"{c['numero']}_{c['ano']}")
        os.makedirs(folder, exist_ok=True)
        
        ok, archivos = buscador.navegar_y_descargar(c['ano'], c['numero'], folder)
        
        if ok:
            LOG.success(f"Archivos descargados: {len(archivos)}")
            for arch in archivos:
                # Simular extraccion basica para ver validacion de CUPS
                try:
                    # Lógica robusta copiada de consolidador
                    df = None
                    last_error = None
                    motores = []
                    
                    if arch.lower().endswith('.xlsb'): motores = ['pyxlsb']
                    elif arch.lower().endswith('.xlsx'): motores = ['openpyxl']
                    elif arch.lower().endswith('.xls'): motores = ['xlrd']
                    
                    # Agregar fallback
                    motores.extend(['openpyxl', 'pyxlsb', 'xlrd', 'odf'])
                    motores = list(dict.fromkeys(motores)) # Unique
                    
                    for eng in motores:
                        try:
                            df = pd.read_excel(arch, engine=eng)
                            break
                        except Exception as e:
                            last_error = e
                            continue
                    
                    if df is None:
                        raise last_error or Exception("No engine worked")

                    LOG.info(f"Leido {os.path.basename(arch)}: {len(df)} filas")
                    # Buscar columnas cups
                    cols = [c for c in df.columns if 'CUPS' in str(c).upper()]
                    if cols:
                        col_cups = cols[0]
                        validos = 0
                        invalidos = 0
                        ejemplos_inv = []
                        for val in df[col_cups].dropna().astype(str):
                            if validar_cups(val): validos +=1
                            else: 
                                invalidos +=1
                                if len(ejemplos_inv) < 5: ejemplos_inv.append(val)
                        
                        LOG.info(f"Validacion CUPS ({col_cups}): {validos} OK, {invalidos} NO")
                        if ejemplos_inv: LOG.warning(f"Ejemplos rechazados: {ejemplos_inv}")
                    else:
                        LOG.warning("No columna CUPS encontrada en primera hoja")
                except Exception as e:
                    LOG.error(f"Error leyendo {arch}: {e}")
        else:
            LOG.error("Fallo navegacion/descarga")

    cliente.desconectar()
    # Limpieza
    # shutil.rmtree(CONFIG.CARPETA_TRABAJO)

if __name__ == '__main__':
    test_contratos()
