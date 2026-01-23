"""
WebSocket de Logs - Consolidador T25
====================================

WebSocket para transmitir logs de procesamiento en tiempo real.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json

router = APIRouter()

# Conexiones activas por job_id
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """Gestiona las conexiones WebSocket."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str):
        """Acepta una nueva conexión WebSocket."""
        await websocket.accept()
        
        if job_id not in self.active_connections:
            self.active_connections[job_id] = set()
        
        self.active_connections[job_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, job_id: str):
        """Elimina una conexión WebSocket."""
        if job_id in self.active_connections:
            self.active_connections[job_id].discard(websocket)
            
            if not self.active_connections[job_id]:
                del self.active_connections[job_id]
    
    async def send_log(self, job_id: str, log: dict):
        """Envía un log a todos los clientes conectados a un job."""
        if job_id not in self.active_connections:
            return
        
        message = json.dumps(log)
        
        disconnected = set()
        for websocket in self.active_connections[job_id]:
            try:
                await websocket.send_text(message)
            except:
                disconnected.add(websocket)
        
        # Limpiar conexiones muertas
        for ws in disconnected:
            self.active_connections[job_id].discard(ws)
    
    async def broadcast_progress(self, job_id: str, progreso: float, mensaje: str):
        """Envía actualización de progreso a todos los clientes."""
        await self.send_log(job_id, {
            "tipo": "progreso",
            "progreso": progreso,
            "mensaje": mensaje
        })


manager = ConnectionManager()


@router.websocket("/ws/logs/{job_id}")
async def websocket_logs(websocket: WebSocket, job_id: str):
    """
    WebSocket para recibir logs de un trabajo en tiempo real.
    
    Conectarse a: ws://localhost:8000/ws/logs/{job_id}
    """
    await manager.connect(websocket, job_id)
    
    try:
        # Importar jobs del módulo de proceso
        from app.api.process import jobs, jobs_lock
        
        last_log_index = 0
        
        while True:
            # Verificar si el job existe
            with jobs_lock:
                if job_id not in jobs:
                    await websocket.send_json({
                        "tipo": "error",
                        "mensaje": "Job no encontrado"
                    })
                    break
                
                job = jobs[job_id]
                
                # Enviar nuevos logs
                logs = job.get("logs", [])
                if len(logs) > last_log_index:
                    for log in logs[last_log_index:]:
                        await websocket.send_json({
                            "tipo": "log",
                            "data": log
                        })
                    last_log_index = len(logs)
                
                # Enviar estado actual
                estado_msg = {
                    "tipo": "estado",
                    "estado": job["estado"],
                    "progreso": job["progreso"],
                    "mensaje": job["mensaje"],
                    "contratos_procesados": job.get("contratos_procesados", 0),
                    "contratos_total": job.get("contratos_total", 0)
                }
            
            await websocket.send_json(estado_msg)
            
            # Si el job terminó, enviar mensaje final y cerrar
            if job["estado"] in ["completado", "error", "cancelado"]:
                with jobs_lock:
                    await websocket.send_json({
                        "tipo": "fin",
                        "estado": job["estado"],
                        "archivos_generados": job.get("archivos_generados", []),
                        "errores": job.get("errores", [])
                    })
                break
            
            # Esperar antes de la siguiente actualización
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "tipo": "error",
                "mensaje": str(e)
            })
        except:
            pass
    finally:
        manager.disconnect(websocket, job_id)


# Función auxiliar para enviar logs desde otros módulos
async def enviar_log(job_id: str, tipo: str, mensaje: str):
    """
    Envía un log a través del WebSocket.
    
    Args:
        job_id: ID del trabajo
        tipo: Tipo de log (info, success, warning, error)
        mensaje: Mensaje del log
    """
    from datetime import datetime
    
    log = {
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "tipo": tipo,
        "mensaje": mensaje
    }
    
    await manager.send_log(job_id, {
        "tipo": "log",
        "data": log
    })
