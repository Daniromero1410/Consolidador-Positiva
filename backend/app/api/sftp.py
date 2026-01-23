"""
API SFTP - Consolidador T25
===========================

Endpoints para conectar, navegar y descargar del servidor SFTP de GoAnywhere.
Incluye navegación completa por carpetas y descarga de archivos.
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os

from app.services.sftp_client import sftp_client
from app.config import CONFIG

router = APIRouter()


@router.get("/sftp/conectar")
async def conectar_sftp():
    """Establece conexión con el servidor SFTP de GoAnywhere."""
    try:
        exito = sftp_client.conectar()
        
        if exito:
            return JSONResponse(content={
                "success": True,
                "message": "Conexión establecida exitosamente",
                "servidor": f"{CONFIG.HOST}:{CONFIG.PORT}"
            })
        else:
            raise HTTPException(
                status_code=500,
                detail="No se pudo establecer conexión con el servidor SFTP"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error de conexión: {str(e)}"
        )


@router.get("/sftp/desconectar")
async def desconectar_sftp():
    """Cierra la conexión SFTP."""
    try:
        sftp_client.desconectar()
        return JSONResponse(content={
            "success": True,
            "message": "Conexión cerrada"
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al desconectar: {str(e)}"
        )


@router.get("/sftp/estado")
async def estado_conexion():
    """Verifica el estado de la conexión SFTP."""
    conectado = sftp_client.esta_conectado()
    
    return JSONResponse(content={
        "conectado": conectado,
        "servidor": f"{CONFIG.HOST}:{CONFIG.PORT}" if conectado else None
    })


@router.get("/sftp/listar")
async def listar_directorio(ruta: str = Query(default=".", description="Ruta del directorio")):
    """Lista el contenido de un directorio en el SFTP."""
    try:
        if not sftp_client.esta_conectado():
            sftp_client.conectar()
        
        items = sftp_client.listar_directorio(ruta)
        
        return JSONResponse(content={
            "success": True,
            "ruta": ruta,
            "cantidad": len(items),
            "items": [
                {
                    "nombre": item.nombre,
                    "tipo": item.tipo.value,
                    "tamaño": item.tamaño,
                    "tamaño_formateado": formatear_tamaño(item.tamaño),
                    "fecha": item.fecha_modificacion,
                    "ruta": item.ruta_completa
                }
                for item in items
            ]
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar directorio: {str(e)}"
        )


@router.get("/sftp/navegar")
async def navegar_directorio(ruta: str = Query(..., description="Ruta del directorio a navegar")):
    """
    Navega a un directorio específico y lista su contenido.
    Devuelve también la ruta padre para navegación hacia atrás.
    """
    try:
        if not sftp_client.esta_conectado():
            conectado = sftp_client.conectar()
            if not conectado:
                raise HTTPException(status_code=500, detail="No se pudo conectar al SFTP")
        
        items = sftp_client.listar_directorio(ruta)
        
        # Calcular ruta padre
        if ruta == "." or ruta == "/" or ruta == CONFIG.CARPETA_PRINCIPAL:
            ruta_padre = None
        else:
            partes = ruta.rstrip('/').rsplit('/', 1)
            ruta_padre = partes[0] if len(partes) > 1 and partes[0] else CONFIG.CARPETA_PRINCIPAL
        
        # Separar carpetas y archivos
        carpetas = [item for item in items if item.tipo.value == "carpeta"]
        archivos = [item for item in items if item.tipo.value == "archivo"]
        
        return JSONResponse(content={
            "success": True,
            "ruta_actual": ruta,
            "ruta_padre": ruta_padre,
            "carpetas": [
                {
                    "nombre": item.nombre,
                    "ruta": item.ruta_completa,
                    "fecha": item.fecha_modificacion
                }
                for item in carpetas
            ],
            "archivos": [
                {
                    "nombre": item.nombre,
                    "ruta": item.ruta_completa,
                    "tamaño": item.tamaño,
                    "tamaño_formateado": formatear_tamaño(item.tamaño),
                    "fecha": item.fecha_modificacion
                }
                for item in archivos
            ],
            "total_carpetas": len(carpetas),
            "total_archivos": len(archivos)
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al navegar: {str(e)}"
        )


@router.get("/sftp/carpeta-principal")
async def listar_carpeta_principal():
    """Lista el contenido de la carpeta principal de contratos."""
    try:
        if not sftp_client.esta_conectado():
            sftp_client.conectar()
        
        items = sftp_client.listar_directorio(CONFIG.CARPETA_PRINCIPAL)
        
        # Filtrar solo carpetas (años de contratos)
        carpetas = [item for item in items if item.tipo.value == "carpeta"]
        
        return JSONResponse(content={
            "success": True,
            "ruta": CONFIG.CARPETA_PRINCIPAL,
            "cantidad": len(carpetas),
            "carpetas": [
                {
                    "nombre": item.nombre,
                    "ruta": item.ruta_completa,
                    "fecha": item.fecha_modificacion
                }
                for item in carpetas
            ]
        })
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al listar carpeta principal: {str(e)}"
        )


@router.get("/sftp/buscar-contrato")
async def buscar_contrato(
    numero: str = Query(..., description="Número del contrato (ej: 45, 662, 946)"),
    año: str = Query(..., description="Año del contrato (ej: 2024, 2025)")
):
    """
    Busca la carpeta de un contrato específico.
    
    El contrato se busca en la carpeta CONTRATOS {año} dentro de la carpeta principal.
    Se prueban variantes con ceros iniciales (45 → 045, 0045).
    
    Retorna la ruta completa para navegar directamente al contrato.
    """
    try:
        if not sftp_client.esta_conectado():
            conectado = sftp_client.conectar()
            if not conectado:
                raise HTTPException(status_code=500, detail="No se pudo conectar al SFTP")
        
        # Limpiar inputs
        numero = numero.strip()
        año = año.strip()
        
        # Construir ruta de la carpeta del año
        carpeta_año = f"{CONFIG.CARPETA_PRINCIPAL}/CONTRATOS {año}"
        
        # Verificar que la carpeta del año existe
        try:
            items_año = sftp_client.listar_directorio(carpeta_año)
        except Exception:
            return JSONResponse(content={
                "success": True,
                "encontrado": False,
                "contrato": f"{numero}-{año}",
                "mensaje": f"No existe la carpeta CONTRATOS {año}",
                "sugerencia": "Verifique que el año sea correcto"
            })
        
        # Generar variantes del número de contrato
        numero_limpio = numero.lstrip('0') or '0'
        variantes = [
            numero_limpio,
            numero_limpio.zfill(2),
            numero_limpio.zfill(3),
            numero_limpio.zfill(4),
            f"0{numero_limpio}",
        ]
        # Eliminar duplicados manteniendo orden
        variantes = list(dict.fromkeys(variantes))
        
        # Buscar carpeta que contenga el número de contrato
        carpeta_encontrada = None
        nombre_carpeta = None
        
        for item in items_año:
            if item.tipo.value != "carpeta":
                continue
            
            nombre_upper = item.nombre.upper()
            
            for variante in variantes:
                # Buscar patrones como "0662 NOMBRE" o "662-2024"
                if nombre_upper.startswith(f"{variante} ") or \
                   nombre_upper.startswith(f"{variante}-") or \
                   nombre_upper.startswith(f"{variante}_") or \
                   f"-{variante}-" in nombre_upper or \
                   f" {variante} " in nombre_upper or \
                   f" {variante}-" in nombre_upper:
                    carpeta_encontrada = item.ruta_completa
                    nombre_carpeta = item.nombre
                    break
            
            if carpeta_encontrada:
                break
        
        if carpeta_encontrada:
            # Listar contenido de la carpeta del contrato
            try:
                contenido = sftp_client.listar_directorio(carpeta_encontrada)
                
                carpetas = [
                    {"nombre": i.nombre, "ruta": i.ruta_completa, "fecha": i.fecha_modificacion}
                    for i in contenido if i.tipo.value == "carpeta"
                ]
                archivos = [
                    {"nombre": i.nombre, "ruta": i.ruta_completa, "tamaño": i.tamaño, 
                     "tamaño_formateado": formatear_tamaño(i.tamaño), "fecha": i.fecha_modificacion}
                    for i in contenido if i.tipo.value == "archivo"
                ]
                
                return JSONResponse(content={
                    "success": True,
                    "encontrado": True,
                    "contrato": f"{numero}-{año}",
                    "carpeta": nombre_carpeta,
                    "ruta": carpeta_encontrada,
                    "ruta_padre": carpeta_año,
                    "contenido": {
                        "carpetas": carpetas,
                        "archivos": archivos,
                        "total_carpetas": len(carpetas),
                        "total_archivos": len(archivos)
                    }
                })
            except Exception as e:
                return JSONResponse(content={
                    "success": True,
                    "encontrado": True,
                    "contrato": f"{numero}-{año}",
                    "carpeta": nombre_carpeta,
                    "ruta": carpeta_encontrada,
                    "ruta_padre": carpeta_año,
                    "error_contenido": str(e)
                })
        else:
            # No encontrado - dar información útil
            return JSONResponse(content={
                "success": True,
                "encontrado": False,
                "contrato": f"{numero}-{año}",
                "mensaje": f"Contrato {numero} no encontrado en CONTRATOS {año}",
                "variantes_buscadas": variantes,
                "carpeta_año": carpeta_año,
                "total_carpetas_año": len([i for i in items_año if i.tipo.value == "carpeta"]),
                "sugerencia": "Verifique el número de contrato o navegue manualmente"
            })
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al buscar contrato: {str(e)}"
        )


@router.get("/sftp/descargar")
async def descargar_archivo_sftp(ruta: str = Query(..., description="Ruta del archivo a descargar")):
    """
    Descarga un archivo del servidor SFTP.
    El archivo se descarga temporalmente al servidor y se envía al cliente.
    """
    try:
        if not sftp_client.esta_conectado():
            conectado = sftp_client.conectar()
            if not conectado:
                raise HTTPException(status_code=500, detail="No se pudo conectar al SFTP")
        
        # Obtener nombre del archivo
        nombre_archivo = os.path.basename(ruta)
        
        # Crear carpeta temporal si no existe
        temp_folder = os.path.join(CONFIG.OUTPUT_FOLDER, "temp_sftp")
        os.makedirs(temp_folder, exist_ok=True)
        
        # Ruta local temporal
        ruta_local = os.path.join(temp_folder, nombre_archivo)
        
        # Descargar archivo
        sftp_client.descargar_archivo(ruta, ruta_local)
        
        # Determinar tipo MIME
        if nombre_archivo.endswith('.xlsx'):
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        elif nombre_archivo.endswith('.xls'):
            media_type = "application/vnd.ms-excel"
        elif nombre_archivo.endswith('.xlsb'):
            media_type = "application/vnd.ms-excel.sheet.binary.macroEnabled.12"
        elif nombre_archivo.endswith('.pdf'):
            media_type = "application/pdf"
        elif nombre_archivo.endswith('.csv'):
            media_type = "text/csv"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=ruta_local,
            filename=nombre_archivo,
            media_type=media_type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al descargar archivo: {str(e)}"
        )


@router.get("/sftp/años-disponibles")
async def obtener_años_disponibles():
    """Obtiene los años de contratos disponibles en el SFTP."""
    try:
        if not sftp_client.esta_conectado():
            sftp_client.conectar()
        
        items = sftp_client.listar_directorio(CONFIG.CARPETA_PRINCIPAL)
        
        años = []
        for item in items:
            if item.tipo.value == "carpeta" and "CONTRATOS" in item.nombre.upper():
                # Extraer año del nombre (ej: "CONTRATOS 2024" → 2024)
                partes = item.nombre.split()
                for parte in partes:
                    if parte.isdigit() and len(parte) == 4:
                        años.append({
                            "año": int(parte),
                            "carpeta": item.nombre,
                            "ruta": item.ruta_completa
                        })
                        break
        
        # Ordenar por año descendente
        años.sort(key=lambda x: x["año"], reverse=True)
        
        return JSONResponse(content={
            "success": True,
            "años": años
        })
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener años: {str(e)}"
        )


def formatear_tamaño(tamaño_bytes: int) -> str:
    """Formatea el tamaño en bytes a una cadena legible."""
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if tamaño_bytes < 1024:
            return f"{tamaño_bytes:.1f} {unidad}"
        tamaño_bytes /= 1024
    return f"{tamaño_bytes:.1f} TB"
