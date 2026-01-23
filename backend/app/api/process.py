"""
API de Procesamiento - Consolidador T25
=======================================

Endpoints para ejecutar el procesamiento de contratos.
Ejecuta el consolidador como subproceso y captura logs en tiempo real.
FILTRADO: Solo muestra logs desde "PROCESAMIENTO" - oculta rutas y pruebas.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import subprocess
import threading
import uuid
import os
import sys
import re
from datetime import datetime
from queue import Queue

from app.config import CONFIG

router = APIRouter()

# Almacén de jobs en memoria
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()


class ProcesamientoRequest(BaseModel):
    año: Optional[int] = None
    numero_contrato: Optional[str] = None
    procesar_todo: Optional[bool] = False


def debe_mostrar_log(linea: str, procesamiento_iniciado: bool) -> tuple[bool, bool]:
    """
    Determina si una línea de log debe mostrarse.
    Retorna (mostrar, procesamiento_iniciado)
    
    Oculta:
    - Rutas de archivos con información sensible
    - Pruebas unitarias
    - Configuración inicial
    - Parámetros recibidos
    """
    linea_upper = linea.upper()
    
    # Detectar inicio de procesamiento real
    if "PROCESAMIENTO V" in linea_upper or "PROCESAMIENTO" in linea_upper and "MODO:" in linea_upper:
        return True, True
    
    # Si no ha iniciado el procesamiento, no mostrar nada
    if not procesamiento_iniciado:
        # Excepción: mostrar línea de inicio
        if "PROCESAMIENTO V" in linea_upper:
            return True, True
        return False, False
    
    # Patrones a OCULTAR (información sensible o irrelevante)
    patrones_ocultar = [
        r'C:\\Users\\',           # Rutas de Windows
        r'/home/',                # Rutas de Linux
        r'OneDrive',              # OneDrive paths
        r'Documentos',            # Documentos folder
        r'\.xlsx$',               # Rutas de archivos Excel
        r'\.xlsb$',
        r'Maestra:.*\\',          # Línea de maestra con ruta
        r'Output:.*\\',           # Línea de output con ruta
        r'PRUEBA \d+:',           # Pruebas unitarias
        r'EJECUTANDO PRUEBAS',    # Inicio de pruebas
        r'RESUMEN DE PRUEBAS',    # Resumen de pruebas
        r'Exitosas:.*Fallidas:',  # Resultados de pruebas
        r'esperado:',             # Resultados de pruebas
        r'Porcentaje:.*%',        # Porcentaje de pruebas
        r'ERRORES ENCONTRADOS',   # Errores de pruebas
        r'retornó.*esperado',     # Resultados de pruebas
        r'Parámetros recibidos',  # Parámetros (contiene rutas)
        r'• Maestra:',            # Detalle de maestra
        r'• Output:',             # Detalle de output
        r'• Modo:',               # Ya se muestra en el header
        r'• Año:',                # Ya se muestra en el header
        r'• Contrato:',           # Ya se muestra en el header
        r'FUNCIONES CORREGIDAS',  # Info técnica
        r'contiene_anexo1\(\)',   # Info técnica
        r'es_telefono_celular',   # Info técnica
        r'validar_cups\(\)',      # Info técnica
        r'validar_tarifa\(\)',    # Info técnica
        r'es_fila_de_traslados',  # Info técnica
        r'buscar_hoja_servicios', # Info técnica
        r'generar_mensaje_hojas', # Info técnica
        r'es_formato_propio',     # Info técnica
        r'SistemaAlertas',        # Info técnica
        r'CORRECCIONES ESPECÍFICAS', # Info técnica
        r'Alerta PAQUETES:',      # Info técnica
        r'Teléfonos: Detecta',    # Info técnica
        r'Inicializando CONSOLIDADOR', # Ya mostrado
        r'uploads\\',             # Rutas de uploads
        r'backend\\',             # Rutas de backend
        r'consolidador-t25-app',  # Nombre del proyecto
    ]
    
    for patron in patrones_ocultar:
        if re.search(patron, linea, re.IGNORECASE):
            return False, procesamiento_iniciado
    
    # Líneas vacías o solo con separadores
    if not linea.strip() or linea.strip() in ['', '─' * 10, '═' * 10, '━' * 10]:
        return False, procesamiento_iniciado
    
    # Líneas que son solo separadores
    if re.match(r'^[═─━\-=\s]+$', linea.strip()):
        return False, procesamiento_iniciado
    
    return True, procesamiento_iniciado


def limpiar_log(linea: str) -> str:
    """Limpia información sensible de una línea de log."""
    # Remover rutas completas, dejar solo nombre de archivo
    linea = re.sub(r'C:\\[^│\n]+\\([^\\│\n]+\.(xlsx|xlsb|xls))', r'\1', linea)
    linea = re.sub(r'/[^│\n]+/([^/│\n]+\.(xlsx|xlsb|xls))', r'\1', linea)
    
    # Remover referencias a OneDrive
    linea = re.sub(r'OneDrive[^│\n]*\\', '', linea)
    
    return linea


def leer_output_proceso(proceso, job_id: str, output_queue: Queue):
    """Lee la salida del proceso línea por línea y actualiza el job."""
    procesamiento_iniciado = False
    
    try:
        for linea in iter(proceso.stdout.readline, ''):
            if not linea:
                break
            
            linea = linea.strip()
            if not linea:
                continue
            
            # Verificar si debemos mostrar este log
            mostrar, procesamiento_iniciado = debe_mostrar_log(linea, procesamiento_iniciado)
            
            if not mostrar:
                continue
            
            # Limpiar información sensible
            linea = limpiar_log(linea)
            
            # Determinar tipo de log basado en contenido
            tipo = "info"
            if "✓" in linea or "éxito" in linea.lower() or "completado" in linea.lower() or "✅" in linea:
                tipo = "success"
            elif "✗" in linea or "error" in linea.lower() or "ERROR" in linea or "❌" in linea:
                tipo = "error"
            elif "⚠" in linea or "advertencia" in linea.lower() or "WARNING" in linea:
                tipo = "warning"
            elif "descargando" in linea.lower() or "↓" in linea or "⬇" in linea:
                tipo = "download"
            elif "archivo" in linea.lower() or "📄" in linea:
                tipo = "file"
            elif "contrato" in linea.lower() or "📋" in linea:
                tipo = "contract"
            elif "procesando" in linea.lower() or "🔄" in linea or "⚙" in linea:
                tipo = "process"
            
            # Extraer progreso si está disponible
            progreso = None
            if "[" in linea and "/" in linea and "]" in linea:
                try:
                    # Buscar patrón [N/M]
                    match = re.search(r'\[(\d+)/(\d+)\]', linea)
                    if match:
                        actual = int(match.group(1))
                        total = int(match.group(2))
                        progreso = (actual / total) * 100
                except:
                    pass
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id]["logs"].append({
                        "timestamp": timestamp,
                        "tipo": tipo,
                        "mensaje": linea
                    })
                    
                    if progreso is not None:
                        jobs[job_id]["progreso"] = progreso
                    
                    jobs[job_id]["mensaje"] = linea[:100]
                    
                    # Actualizar contrato actual si se detecta
                    if "contrato" in linea.lower() and ("procesando" in linea.lower() or "iniciando" in linea.lower() or "[" in linea):
                        jobs[job_id]["contrato_actual"] = linea
                        
    except Exception as e:
        print(f"Error leyendo output: {e}")


def ejecutar_consolidador_subproceso(
    job_id: str,
    archivo_maestra: str,
    modo: str,
    año: Optional[str],
    numero_contrato: Optional[str]
):
    """Ejecuta el consolidador como subproceso."""
    try:
        # Convertir ruta de maestra a absoluta
        archivo_maestra_absoluto = os.path.abspath(archivo_maestra)
        
        if not os.path.exists(archivo_maestra_absoluto):
            raise FileNotFoundError(f"Archivo de maestra no encontrado")
        
        # Configurar variables de entorno
        env = os.environ.copy()
        env["CONSOLIDADOR_MAESTRA"] = archivo_maestra_absoluto
        env["CONSOLIDADOR_MODO"] = modo
        env["CONSOLIDADOR_OUTPUT"] = os.path.abspath(CONFIG.OUTPUT_FOLDER)
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        
        if año:
            env["CONSOLIDADOR_ANO"] = str(año)
        if numero_contrato:
            env["CONSOLIDADOR_NUMERO"] = str(numero_contrato)
        
        # Credenciales SFTP
        env["SFTP_HOST"] = CONFIG.HOST
        env["SFTP_PORT"] = str(CONFIG.PORT)
        env["SFTP_USERNAME"] = CONFIG.USERNAME
        env["SFTP_PASSWORD"] = CONFIG.PASSWORD
        env["SFTP_CARPETA_PRINCIPAL"] = CONFIG.CARPETA_PRINCIPAL
        
        # Ruta al script
        script_path = os.path.join(
            os.path.dirname(__file__),
            "..", "core", "consolidador_t25_parametrizado.py"
        )
        script_path = os.path.abspath(script_path)
        
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script del consolidador no encontrado")
        
        with jobs_lock:
            jobs[job_id]["mensaje"] = "Iniciando consolidador..."
            jobs[job_id]["estado"] = "en_proceso"
        
        # Ejecutar proceso
        proceso = subprocess.Popen(
            [sys.executable, "-u", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env=env,
            cwd=os.path.dirname(script_path),
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )
        
        # Leer output
        output_queue = Queue()
        lector_thread = threading.Thread(
            target=leer_output_proceso,
            args=(proceso, job_id, output_queue)
        )
        lector_thread.start()
        
        proceso.wait()
        lector_thread.join(timeout=5)
        
        exit_code = proceso.returncode
        
        # Buscar archivos generados
        archivos_generados = []
        output_folder = os.path.abspath(CONFIG.OUTPUT_FOLDER)
        
        if os.path.exists(output_folder):
            ahora = datetime.now()
            for archivo in os.listdir(output_folder):
                filepath = os.path.join(output_folder, archivo)
                if os.path.isfile(filepath):
                    mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if (ahora - mtime).total_seconds() < 600:
                        archivos_generados.append(archivo)
        
        with jobs_lock:
            if exit_code == 0:
                jobs[job_id]["estado"] = "completado"
                jobs[job_id]["progreso"] = 100
                jobs[job_id]["mensaje"] = "Procesamiento completado exitosamente"
            else:
                jobs[job_id]["estado"] = "error"
                jobs[job_id]["mensaje"] = f"Proceso terminó con código {exit_code}"
            
            jobs[job_id]["fin"] = datetime.now().isoformat()
            jobs[job_id]["archivos_generados"] = archivos_generados
            
            logs = jobs[job_id]["logs"]
            jobs[job_id]["estadisticas"] = {
                "total_logs": len(logs),
                "errores": len([l for l in logs if l["tipo"] == "error"]),
                "advertencias": len([l for l in logs if l["tipo"] == "warning"]),
                "descargas": len([l for l in logs if l["tipo"] == "download"])
            }
        
    except Exception as e:
        import traceback
        error_msg = str(e)
        
        with jobs_lock:
            jobs[job_id]["estado"] = "error"
            jobs[job_id]["mensaje"] = error_msg
            jobs[job_id]["errores"].append(error_msg)
            jobs[job_id]["fin"] = datetime.now().isoformat()
            jobs[job_id]["logs"].append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "tipo": "error",
                "mensaje": f"Error: {error_msg}"
            })


@router.post("/procesar")
async def iniciar_procesamiento(request: ProcesamientoRequest):
    """Inicia el procesamiento de contratos."""
    from app.api.upload import maestra_actual, archivo_maestra_path
    
    if maestra_actual is None:
        raise HTTPException(status_code=400, detail="No hay maestra cargada. Suba un archivo primero.")
    
    if not archivo_maestra_path:
        raise HTTPException(status_code=400, detail="Ruta de maestra no disponible.")
    
    ruta_absoluta = os.path.abspath(archivo_maestra_path)
    if not os.path.exists(ruta_absoluta):
        raise HTTPException(status_code=400, detail="Archivo de maestra no encontrado")
    
    # Determinar modo
    if request.procesar_todo:
        modo = "COMPLETO"
        año = None
        numero = None
    elif request.año and request.numero_contrato:
        modo = "ESPECIFICO"
        año = str(request.año)
        numero = request.numero_contrato
    elif request.año:
        modo = "POR_ANO"
        año = str(request.año)
        numero = None
    else:
        raise HTTPException(status_code=400, detail="Debe especificar año, contrato específico o procesar_todo=true")
    
    contratos = maestra_actual.obtener_contratos_para_procesar(
        año=int(año) if año else None,
        numero_contrato=numero
    )
    
    job_id = str(uuid.uuid4())
    
    with jobs_lock:
        jobs[job_id] = {
            "job_id": job_id,
            "estado": "pendiente",
            "progreso": 0,
            "mensaje": "Iniciando...",
            "modo": modo,
            "año": año,
            "numero_contrato": numero,
            "contratos_total": len(contratos),
            "contratos_procesados": 0,
            "contrato_actual": "",
            "inicio": datetime.now().isoformat(),
            "fin": None,
            "archivos_generados": [],
            "errores": [],
            "logs": [],
            "estadisticas": {}
        }
    
    thread = threading.Thread(
        target=ejecutar_consolidador_subproceso,
        args=(job_id, ruta_absoluta, modo, año, numero)
    )
    thread.daemon = True
    thread.start()
    
    return JSONResponse(content={
        "success": True,
        "job_id": job_id,
        "modo": modo,
        "mensaje": f"Procesamiento iniciado para {len(contratos)} contratos",
        "contratos_estimados": len(contratos)
    })


@router.get("/procesar/estado/{job_id}")
async def get_estado_job(job_id: str):
    """Obtiene el estado actual de un job."""
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        
        job = jobs[job_id].copy()
        job["total_logs"] = len(job["logs"])
        del job["logs"]
        
        return JSONResponse(content=job)


@router.get("/procesar/logs/{job_id}")
async def get_logs_job(job_id: str, desde: int = 0):
    """Obtiene los logs de un job desde un índice específico."""
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        
        job = jobs[job_id]
        logs = job["logs"][desde:]
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            "estado": job["estado"],
            "progreso": job["progreso"],
            "mensaje": job["mensaje"],
            "contrato_actual": job.get("contrato_actual", ""),
            "total_logs": len(job["logs"]),
            "logs": logs,
            "archivos_generados": job.get("archivos_generados", [])
        })


@router.delete("/procesar/cancelar/{job_id}")
async def cancelar_job(job_id: str):
    """Cancela un job en ejecución."""
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        
        jobs[job_id]["estado"] = "cancelado"
        jobs[job_id]["mensaje"] = "Cancelado por el usuario"
        jobs[job_id]["fin"] = datetime.now().isoformat()
        
        return JSONResponse(content={"success": True, "mensaje": "Job cancelado"})


@router.get("/procesar/historial")
async def get_historial():
    """Obtiene el historial de jobs."""
    with jobs_lock:
        historial = []
        for job_id, job in sorted(jobs.items(), key=lambda x: x[1]["inicio"], reverse=True):
            historial.append({
                "job_id": job_id,
                "estado": job["estado"],
                "modo": job["modo"],
                "año": job.get("año"),
                "contratos_total": job["contratos_total"],
                "inicio": job["inicio"],
                "fin": job.get("fin"),
                "archivos_generados": len(job.get("archivos_generados", []))
            })
        
        return JSONResponse(content={"success": True, "historial": historial})


@router.get("/procesar/job/{job_id}/archivos")
async def get_archivos_job(job_id: str):
    """Obtiene la lista de archivos generados por un job."""
    with jobs_lock:
        if job_id not in jobs:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        
        archivos = jobs[job_id].get("archivos_generados", [])
        
        archivos_info = []
        for archivo in archivos:
            filepath = os.path.join(CONFIG.OUTPUT_FOLDER, archivo)
            if os.path.exists(filepath):
                archivos_info.append({
                    "nombre": archivo,
                    "tamaño": os.path.getsize(filepath),
                    "ruta_descarga": f"/api/descargas/archivo/{archivo}"
                })
        
        return JSONResponse(content={"success": True, "job_id": job_id, "archivos": archivos_info})
