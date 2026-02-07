
import re
import sys
import os
import pandas as pd

# ==========================================
# LOGICA A PROBAR (Copiada de v15.2)
# ==========================================

def es_archivo_tarifas_valido(nombre: str) -> tuple:
    if not nombre:
        return False, 'INVALIDO'

    # 🆕 v15.2: Normalización agresiva (eliminar tabs y espacios extra)
    nombre_upper = nombre.upper().replace('\t', '').strip()

    # EXCLUSIONES
    if re.search(r'AN[AÁ]LISIS\s*(DE\s*)?(TARIFAS?|TARIFA)', nombre_upper):
        return False, 'INVALIDO'

    # DETECCIÓN 1: OTROSÍ
    patrones_otrosi = [
        r'OTRO\s*S[IÍ]\s*[_#\-\s]*(\d+)',
        r'OTROS[IÍ]\s*[_#\-\s]*(\d+)',
        r'OT[_\-\s]?(\d+)',
        r'ADICI[OÓ]N\s*[_#\-\s]*(\d+)',
        r'MODIFICACI[OÓ]N\s*[_#\-\s]*(\d+)',
    ]
    for patron in patrones_otrosi:
        if re.search(patron, nombre_upper):
            return True, 'OTROSI'

    # DETECCIÓN 2: ANEXO 1
    patrones_anexo1 = [
        r'ANEXO\s*[_\-\s]*0?1(?!\d)',
        r'ANEX[O0]\s*[_\-\s]*1(?!\d)',
        r'ANEXO\s*N[OÚº°]?\.?\s*0?1(?!\d)',
        r'A1[_\-\s]',
        r'[_\-]ANEXO[_\-]?1',
        r'ANEXO[_\-]1[_\-]',
    ]

    for patron in patrones_anexo1:
        if re.search(patron, nombre_upper):
            return True, 'ANEXO_1'

    n_limpio = nombre_upper.replace(' ', '').replace('_', '').replace('-', '').replace('(', '').replace(')', '')
    if 'ANEXO1' in n_limpio or 'ANEXO01' in n_limpio:
        return True, 'ANEXO_1'

    # EXCLUSIÓN: Anexo 2-9
    patron_anexo_no_1 = r'ANEXO\s*[_\-\s]*([2-9]|[1-9]\d)(?!\d)'
    if re.search(patron_anexo_no_1, nombre_upper):
        return False, 'INVALIDO'

    # DETECCIÓN 3: TARIFAS
    patrones_tarifas = [
        r'\d+[\-_]TARIFAS[\-_]',
        r'^TARIFAS[\-_]',
        r'[\-_]TARIFAS[\-_]',
        r'[\-_]TARIFAS\.',
    ]
    for patron in patrones_tarifas:
        if re.search(patron, nombre_upper):
            return True, 'TARIFAS'

    if 'ANEXO' in nombre_upper and ('TARIFA' in nombre_upper or 'SERV' in nombre_upper):
        otros_anexos = re.search(r'ANEXO\s*[_\-\s]*([2-9]|[1-9]\d)(?!\d)', nombre_upper)
        if not otros_anexos:
            return True, 'ANEXO_1'

    return False, 'INVALIDO'

HOJAS_EXCLUIR_SILENCIOSAMENTE = {
    'INSTRUCCIONES', 'INFO', 'DATOS', 'CONTENIDO', 'INDICE', 'ÍNDICE',
    'GUIA DE USO', 'GUÍA DE USO', 'CONTROL DE CAMBIOS', 'HOJA1', 'SHEET1',
    'INSTRUCTIVO', 'PARAMETROS', 'PARÁMETROS', 'CONFIGURACION', 'CONFIGURACIÓN',
    'LISTA', 'LISTAS', 'VALIDACION', 'VALIDACIÓN', 'CATALOGO', 'CATÁLOGO',
    'RESUMEN', 'PORTADA', 'CARATULA', 'CARÁTULA', 'INICIO', 'HOME',
    'MENU', 'MENÚ', 'ANEXO TECNICO', 'ANEXO TÉCNICO', 'GLOSARIO',
}
HOJAS_SIN_SERVICIOS_VALIDOS = {
    'PAQUETES', 'TARIFAS PAQUETES', 'PAQUETE',
    'COSTO VIAJE', 'COSTO DE VIAJE', 'COSTOS VIAJE',
}

def debe_excluir_hoja_silenciosamente(nombre_hoja: str) -> bool:
    if not nombre_hoja: return True
    nombre_upper = nombre_hoja.upper().strip()
    if nombre_upper in HOJAS_EXCLUIR_SILENCIOSAMENTE: return True
    if nombre_upper in HOJAS_SIN_SERVICIOS_VALIDOS: return True
    for patron in HOJAS_SIN_SERVICIOS_VALIDOS:
        if patron in nombre_upper: return True
    return False

def buscar_hoja_servicios_inteligente(hojas: list) -> tuple:
    if not hojas: return None, []
    hojas_norm = {h: h.upper().strip() for h in hojas}
    hojas_excluidas_info = []
    
    hojas_validas = {h: h_norm for h, h_norm in hojas_norm.items()
                     if not debe_excluir_hoja_silenciosamente(h_norm)}

    if not hojas_validas:
        print("DEBUG: Todas las hojas fueron excluidas.")
        hojas_validas = hojas_norm

    print(f"DEBUG: Hojas válidas para búsqueda: {list(hojas_validas.values())}")

    # PASO 1: SERVICIOS
    for hoja, h_norm in hojas_validas.items():
        if h_norm.strip() == 'SERVICIOS': return hoja, []

    # PASO 2: TARIFAS DE SERVICIOS
    patrones_exactos = ['TARIFAS DE SERVICIOS', 'TARIFA DE SERVICIOS', 'TARIFAS DE SERV', 'TARIFA DE SERV', 'TARIFAS DE SERVICIO', 'TARIFA DE SERVICIO']
    for hoja, h_norm in hojas_validas.items():
        h_clean = ' '.join(h_norm.split())
        for patron in patrones_exactos:
            if h_clean == patron or h_clean.startswith(patron + ' ') or h_clean.startswith(patron):
                if 'COSTO' not in h_clean and 'VIAJE' not in h_clean and 'PAQUETE' not in h_clean:
                    return hoja, []

    # PASO 3: TARIFA + SERV
    for hoja, h_norm in hojas_validas.items():
        if 'TARIFA' in h_norm and 'SERV' in h_norm:
            if 'TRASLADO' not in h_norm and 'PAQUETE' not in h_norm:
                return hoja, []

    # PASO 4: SERVICIO
    for hoja, h_norm in hojas_validas.items():
        if 'SERVICIO' in h_norm and 'TRASLADO' not in h_norm:
            return hoja, []

    # PASO 5: CUPS
    for hoja, h_norm in hojas_validas.items():
        if 'CUPS' in h_norm:
            if not debe_excluir_hoja_silenciosamente(h_norm):
                return hoja, []

    # PASO 6: ANEXO 1 (MEJORADO)
    patrones_anexo1_hoja = [r'ANEXO\s*[_\-\s]*0?1', r'ANEXO\s*N[OÚº°]?\.?\s*0?1', r'^0?1$']
    for hoja, h_norm in hojas_validas.items():
        for pat in patrones_anexo1_hoja:
            if re.search(pat, h_norm): return hoja, []
        
        h_clean = h_norm.replace(' ', '').replace('_', '').replace('.', '')
        if h_clean in ['ANEXO1', 'ANEXO01', 'HOJA1', 'A1']:
            return hoja, []

    # PASO 7: TARIFAS Generico
    for hoja, h_norm in hojas_validas.items():
        if h_norm in ['TARIFAS', 'TARIFA', 'LISTA DE TARIFAS']:
            return hoja, []
        if 'TARIFAS' in h_norm or 'TARIFA' in h_norm:
            if not any(x in h_norm for x in ['PAQUETE', 'COSTO', 'VIAJE', 'AMBULANCIA', 'TRASLADO']):
                return hoja, []

    return None, []

# ==========================================
# DIAGNOSTICO
# ==========================================

archivo = "ACT1-ANEXO 1-0531-2024-HABITALSALUD.xlsb"
path = r"c:\Users\daniel.romero\OneDrive - GESTAR INNOVACION S.A.S\Documentos\CONSOLIDADOR POSITIVA\ACT1-ANEXO 1-0531-2024-HABITALSALUD.xlsb"

print(f"--- DIAGNOSTICO PARA: {archivo} ---")

# 1. Validar nombre
valido, tipo = es_archivo_tarifas_valido(archivo)
print(f"1. Validación de nombre: Es válido? {valido} | Tipo: {tipo}")
if not valido:
    print("❌ ERROR: El nombre del archivo es rechazado.")
else:
    print("✅ El nombre del archivo es aceptado.")

# 2. Verificar librería pyxlsb
try:
    import pyxlsb
    print("2. Librería 'pyxlsb': INSTALADA ✅")
except ImportError:
    print("2. Librería 'pyxlsb': NO INSTALADA ❌ (Necesaria para .xlsb)")

# 3. Leer hojas reales
if os.path.exists(path):
    print(f"3. Leyendo archivo en: {path}")
    try:
        xls = pd.ExcelFile(path, engine='pyxlsb')
        hojas = xls.sheet_names
        print(f"   Hojas encontradas: {hojas}")
        
        # 4. Probar búsqueda de hoja
        hoja_sel, _ = buscar_hoja_servicios_inteligente(hojas)
        if hoja_sel:
            print(f"✅ Hoja seleccionada: '{hoja_sel}'")
        else:
            print("❌ ERROR: No se encontró hoja de servicios válida.")
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
else:
    print(f"⚠️ El archivo no existe en la ruta especificada: {path}")
