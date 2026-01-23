"""
API de Upload - Consolidador T25
================================

Maneja la subida y análisis del archivo de maestra de contratos.
Incluye persistencia automática y caché para respuestas rápidas.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
import json
from typing import Optional
from datetime import datetime

from app.config import CONFIG
from app.services.maestra_parser import MaestraParser

router = APIRouter()

# Variables globales
maestra_actual: Optional[MaestraParser] = None
archivo_maestra_path: Optional[str] = None
cache_resumen: Optional[dict] = None  # Caché para evitar re-parsear

# Archivo para persistir el estado
ESTADO_FILE = os.path.join(CONFIG.UPLOAD_FOLDER, ".maestra_estado.json")


def guardar_estado():
    """Guarda el estado actual de la maestra en un archivo JSON."""
    global archivo_maestra_path, cache_resumen
    
    try:
        os.makedirs(CONFIG.UPLOAD_FOLDER, exist_ok=True)
        
        estado = {
            "archivo": archivo_maestra_path,
            "fecha_carga": datetime.now().isoformat(),
            "cache_resumen": cache_resumen
        }
        
        with open(ESTADO_FILE, 'w', encoding='utf-8') as f:
            json.dump(estado, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Estado guardado: {archivo_maestra_path}")
        return True
    except Exception as e:
        print(f"❌ Error guardando estado: {e}")
        return False


def cargar_estado_inicial():
    """Carga la maestra guardada previamente si existe."""
    global maestra_actual, archivo_maestra_path, cache_resumen
    
    try:
        if not os.path.exists(ESTADO_FILE):
            print("📂 No hay estado previo guardado")
            return False
        
        with open(ESTADO_FILE, 'r', encoding='utf-8') as f:
            estado = json.load(f)
        
        archivo = estado.get("archivo")
        
        if not archivo or not os.path.exists(archivo):
            print(f"⚠️ Archivo de maestra no existe: {archivo}")
            os.remove(ESTADO_FILE)
            return False
        
        print(f"📂 Cargando maestra guardada: {archivo}")
        
        # Cargar caché si existe
        cache_resumen = estado.get("cache_resumen")
        
        # Crear parser (pero no parsear aún si hay caché)
        maestra_actual = MaestraParser(archivo)
        archivo_maestra_path = archivo
        
        # Si no hay caché, parsear ahora
        if not cache_resumen:
            cache_resumen = maestra_actual.parse()
            guardar_estado()  # Guardar con caché
        
        print(f"✅ Maestra cargada: {cache_resumen.get('total_contratos', 0)} contratos")
        return True
        
    except Exception as e:
        print(f"❌ Error cargando estado inicial: {e}")
        maestra_actual = None
        archivo_maestra_path = None
        cache_resumen = None
        return False


def limpiar_estado():
    """Elimina el archivo de estado."""
    global maestra_actual, archivo_maestra_path, cache_resumen
    
    try:
        if os.path.exists(ESTADO_FILE):
            os.remove(ESTADO_FILE)
        maestra_actual = None
        archivo_maestra_path = None
        cache_resumen = None
    except Exception as e:
        print(f"Error limpiando estado: {e}")


# Cargar estado al importar el módulo
print("🔄 Inicializando módulo de upload...")
cargar_estado_inicial()


@router.post("/upload/maestra")
async def upload_maestra(file: UploadFile = File(...)):
    """Sube el archivo de maestra de contratos."""
    global maestra_actual, archivo_maestra_path, cache_resumen
    
    # Validar extensión
    filename = file.filename
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in ['.xlsx', '.xls', '.xlsb', '.xlsm']:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {ext}. Use .xlsx, .xls, .xlsb o .xlsm"
        )
    
    # Crear carpeta si no existe
    os.makedirs(CONFIG.UPLOAD_FOLDER, exist_ok=True)
    
    # Guardar archivo con nombre único para evitar conflictos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_filename = f"maestra_{timestamp}{ext}"
    filepath = os.path.join(CONFIG.UPLOAD_FOLDER, safe_filename)
    
    try:
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar archivo: {str(e)}")
    
    # Parsear maestra
    try:
        maestra_actual = MaestraParser(filepath)
        resultado = maestra_actual.parse()
        archivo_maestra_path = filepath
        cache_resumen = resultado  # Guardar en caché
        
        # Guardar estado inmediatamente
        if guardar_estado():
            print(f"✅ Maestra guardada y persistida: {filepath}")
        
        return JSONResponse(content={
            "success": True,
            "filename": filename,
            "mensaje": f"Maestra cargada: {resultado.get('total_contratos', 0)} contratos",
            "resumen": resultado
        })
        
    except Exception as e:
        # Si falla, eliminar archivo
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=f"Error al procesar maestra: {str(e)}")


@router.get("/maestra/resumen")
async def get_maestra_resumen():
    """Obtiene el resumen de la maestra (usa caché)."""
    global cache_resumen, maestra_actual
    
    if maestra_actual is None:
        raise HTTPException(status_code=404, detail="No hay maestra cargada")
    
    # Usar caché si existe
    if cache_resumen:
        return JSONResponse(content={"success": True, "resumen": cache_resumen})
    
    # Si no hay caché, parsear
    try:
        cache_resumen = maestra_actual.parse()
        guardar_estado()
        return JSONResponse(content={"success": True, "resumen": cache_resumen})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/maestra/contratos")
async def get_contratos(año: Optional[int] = None, numero: Optional[str] = None):
    """Obtiene los contratos según los filtros."""
    global maestra_actual
    
    if maestra_actual is None:
        raise HTTPException(status_code=404, detail="No hay maestra cargada")
    
    try:
        contratos = maestra_actual.obtener_contratos_para_procesar(año=año, numero_contrato=numero)
        return JSONResponse(content={"success": True, "cantidad": len(contratos), "contratos": contratos})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/maestra/contratos/todos")
async def get_todos_contratos():
    """Obtiene todos los contratos de la maestra con información detallada para la tabla."""
    global maestra_actual, cache_resumen
    
    if maestra_actual is None:
        raise HTTPException(status_code=404, detail="No hay maestra cargada")
    
    try:
        contratos = []
        df = maestra_actual.df
        
        if df is None:
            # Si el dataframe no está cargado, parsear
            maestra_actual.parse()
            df = maestra_actual.df
        
        if df is None:
            raise HTTPException(status_code=500, detail="No se pudo cargar el dataframe")
        
        # Detectar nombres de columnas (pueden variar según el archivo)
        col_numero = None
        col_año = None
        col_razon = None
        col_nit = None
        col_depto = None
        col_muni = None
        
        for col in df.columns:
            col_upper = str(col).upper().strip()
            if col_numero is None and any(x in col_upper for x in ['NO_CONTRATO', 'CONTRATO', 'NUMERO', 'N°']):
                col_numero = col
            if col_año is None and any(x in col_upper for x in ['AÑO', 'ANO', 'YEAR']):
                col_año = col
            if col_razon is None and any(x in col_upper for x in ['RAZON_SOCIAL', 'RAZON', 'PRESTADOR', 'NOMBRE']):
                col_razon = col
            if col_nit is None and any(x in col_upper for x in ['NIT', 'IDENTIFICACION', 'DOCUMENTO']):
                col_nit = col
            if col_depto is None and any(x in col_upper for x in ['DEPARTAMENTO', 'DEPTO', 'DPTO']):
                col_depto = col
            if col_muni is None and any(x in col_upper for x in ['MUNICIPIO', 'CIUDAD', 'MUNI']):
                col_muni = col
        
        for idx, row in df.iterrows():
            try:
                # Obtener número de contrato
                numero = ''
                if col_numero:
                    numero = str(row.get(col_numero, '')).strip()
                
                if not numero or numero == 'nan' or numero == '':
                    continue
                
                # Obtener año
                año = 0
                if col_año:
                    try:
                        año_val = row.get(col_año, 0)
                        if año_val and str(año_val) != 'nan':
                            año = int(float(str(año_val)))
                    except:
                        pass
                
                # Obtener razón social
                razon_social = ''
                if col_razon:
                    razon_social = str(row.get(col_razon, '')).strip()
                    if razon_social == 'nan':
                        razon_social = ''
                
                # Obtener NIT
                nit = ''
                if col_nit:
                    nit = str(row.get(col_nit, '')).strip()
                    if nit == 'nan':
                        nit = ''
                
                # Obtener departamento
                departamento = ''
                if col_depto:
                    departamento = str(row.get(col_depto, '')).strip()
                    if departamento == 'nan':
                        departamento = ''
                
                # Obtener municipio
                municipio = ''
                if col_muni:
                    municipio = str(row.get(col_muni, '')).strip()
                    if municipio == 'nan':
                        municipio = ''
                
                contrato = {
                    "numero": numero,
                    "año": año,
                    "razon_social": razon_social,
                    "nit": nit,
                    "departamento": departamento,
                    "municipio": municipio
                }
                
                contratos.append(contrato)
                
            except Exception as row_error:
                print(f"Error procesando fila {idx}: {row_error}")
                continue
        
        return JSONResponse(content={
            "success": True,
            "total": len(contratos),
            "contratos": contratos
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en get_todos_contratos: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error obteniendo contratos: {str(e)}")


@router.get("/maestra/años")
async def get_años_disponibles():
    """Obtiene los años disponibles (usa caché)."""
    global cache_resumen, maestra_actual
    
    if maestra_actual is None:
        raise HTTPException(status_code=404, detail="No hay maestra cargada")
    
    try:
        # Usar caché
        if not cache_resumen:
            cache_resumen = maestra_actual.parse()
            guardar_estado()
        
        años = cache_resumen.get('años_disponibles', [])
        contratos_por_año = cache_resumen.get('contratos_por_año', {})
        
        años_info = [
            {"año": año, "cantidad_contratos": contratos_por_año.get(str(año), {}).get('cantidad', 0)}
            for año in años
        ]
        
        return JSONResponse(content={"success": True, "años": años_info})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/maestra")
async def eliminar_maestra():
    """Elimina la maestra cargada."""
    global maestra_actual, archivo_maestra_path, cache_resumen
    
    try:
        # Eliminar archivo físico
        if archivo_maestra_path and os.path.exists(archivo_maestra_path):
            os.remove(archivo_maestra_path)
        
        limpiar_estado()
        
        return JSONResponse(content={"success": True, "mensaje": "Maestra eliminada"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/maestra/estado")
async def get_estado_maestra():
    """Obtiene el estado actual de la maestra (respuesta rápida)."""
    global maestra_actual, archivo_maestra_path, cache_resumen
    
    if maestra_actual is None or archivo_maestra_path is None:
        return JSONResponse(content={
            "cargada": False,
            "archivo": None,
            "mensaje": "No hay maestra cargada"
        })
    
    # Respuesta rápida usando caché
    return JSONResponse(content={
        "cargada": True,
        "archivo": os.path.basename(archivo_maestra_path),
        "ruta": archivo_maestra_path,
        "total_contratos": cache_resumen.get('total_contratos', 0) if cache_resumen else 0,
        "total_prestadores": cache_resumen.get('total_prestadores', 0) if cache_resumen else 0,
        "años_disponibles": cache_resumen.get('años_disponibles', []) if cache_resumen else []
    })


@router.post("/maestra/recargar")
async def recargar_maestra():
    """Fuerza recarga de la maestra desde el archivo."""
    global maestra_actual, archivo_maestra_path, cache_resumen
    
    if not archivo_maestra_path or not os.path.exists(archivo_maestra_path):
        raise HTTPException(status_code=404, detail="No hay archivo de maestra para recargar")
    
    try:
        maestra_actual = MaestraParser(archivo_maestra_path)
        cache_resumen = maestra_actual.parse()
        guardar_estado()
        
        return JSONResponse(content={
            "success": True,
            "mensaje": "Maestra recargada",
            "total_contratos": cache_resumen.get('total_contratos', 0)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
