"""
API de Descargas - Consolidador T25
===================================

Endpoints para listar y descargar archivos generados.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
import os
import zipfile
from typing import List

from app.config import CONFIG

router = APIRouter()


def formatear_tamaño(tamaño_bytes: int) -> str:
    """Formatea el tamaño en bytes a una cadena legible."""
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if tamaño_bytes < 1024:
            return f"{tamaño_bytes:.1f} {unidad}"
        tamaño_bytes /= 1024
    return f"{tamaño_bytes:.1f} TB"


@router.get("/descargas/listar")
async def listar_archivos_disponibles():
    """Lista los archivos disponibles para descargar."""
    from datetime import datetime
    archivos = []

    try:
        if not os.path.exists(CONFIG.OUTPUT_FOLDER):
            os.makedirs(CONFIG.OUTPUT_FOLDER, exist_ok=True)

        for filename in os.listdir(CONFIG.OUTPUT_FOLDER):
            filepath = os.path.join(CONFIG.OUTPUT_FOLDER, filename)

            if os.path.isfile(filepath):
                tamaño = os.path.getsize(filepath)
                fecha_timestamp = os.path.getmtime(filepath)
                fecha_formateada = datetime.fromtimestamp(fecha_timestamp).strftime('%d/%m/%Y %H:%M')

                archivos.append({
                    "nombre": filename,
                    "tamaño": tamaño,
                    "tamaño_formateado": formatear_tamaño(tamaño),
                    "fecha_modificacion": fecha_formateada,
                    "fecha_modificacion_timestamp": fecha_timestamp,
                    "ruta": f"/outputs/{filename}"
                })

        # Ordenar por fecha descendente
        archivos.sort(key=lambda x: x["fecha_modificacion_timestamp"], reverse=True)
        
        return JSONResponse(content={
            "success": True,
            "cantidad": len(archivos),
            "archivos": archivos
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar archivos: {str(e)}"
        )


@router.get("/descargas/archivo/{filename}")
async def descargar_archivo(filename: str):
    """Descarga un archivo específico."""
    filepath = os.path.join(CONFIG.OUTPUT_FOLDER, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado: {filename}"
        )
    
    # Determinar tipo MIME
    if filename.endswith('.xlsx'):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif filename.endswith('.xls'):
        media_type = "application/vnd.ms-excel"
    elif filename.endswith('.csv'):
        media_type = "text/csv"
    elif filename.endswith('.zip'):
        media_type = "application/zip"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type=media_type
    )


@router.post("/descargas/zip")
async def descargar_multiples(archivos: List[str]):
    """Crea un ZIP con múltiples archivos y lo descarga."""
    if not archivos:
        raise HTTPException(
            status_code=400,
            detail="Debe especificar al menos un archivo"
        )
    
    # Verificar que todos los archivos existen
    for filename in archivos:
        filepath = os.path.join(CONFIG.OUTPUT_FOLDER, filename)
        if not os.path.exists(filepath):
            raise HTTPException(
                status_code=404,
                detail=f"Archivo no encontrado: {filename}"
            )
    
    # Crear ZIP
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"consolidado_{timestamp}.zip"
    zip_filepath = os.path.join(CONFIG.OUTPUT_FOLDER, zip_filename)
    
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for filename in archivos:
                filepath = os.path.join(CONFIG.OUTPUT_FOLDER, filename)
                zipf.write(filepath, filename)
        
        return FileResponse(
            path=zip_filepath,
            filename=zip_filename,
            media_type="application/zip"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear ZIP: {str(e)}"
        )


@router.delete("/descargas/archivo/{filename}")
async def eliminar_archivo(filename: str):
    """Elimina un archivo del servidor."""
    filepath = os.path.join(CONFIG.OUTPUT_FOLDER, filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(
            status_code=404,
            detail=f"Archivo no encontrado: {filename}"
        )
    
    try:
        os.remove(filepath)
        return JSONResponse(content={
            "success": True,
            "mensaje": f"Archivo {filename} eliminado"
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar archivo: {str(e)}"
        )


@router.delete("/descargas/limpiar")
async def limpiar_archivos():
    """Elimina todos los archivos de la carpeta de salida."""
    try:
        eliminados = 0
        for filename in os.listdir(CONFIG.OUTPUT_FOLDER):
            filepath = os.path.join(CONFIG.OUTPUT_FOLDER, filename)
            if os.path.isfile(filepath):
                os.remove(filepath)
                eliminados += 1
        
        return JSONResponse(content={
            "success": True,
            "mensaje": f"{eliminados} archivos eliminados"
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al limpiar archivos: {str(e)}"
        )
