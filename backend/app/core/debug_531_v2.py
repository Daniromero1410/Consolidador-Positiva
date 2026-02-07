
import re
import sys
import os
import pandas as pd

# Redirigir stdout
sys.stdout = open('debug_531.log', 'w', encoding='utf-8')

# ==========================================
# LOGICA A PROBAR (Mismos cambios v15.2)
# ==========================================

def es_archivo_tarifas_valido(nombre: str) -> tuple:
    if not nombre: return False, 'INVALIDO'

    # Sanitización: Tab, espacio, non-breaking space
    nombre_upper = nombre.upper().replace('\t', '').strip()
    
    # print(f"DEBUG: Nombre sanitizado: '{nombre_upper}'")

    # Regex checks
    patrones_anexo1 = [
        r'ANEXO\s*[_\-\s]*0?1(?!\d)',
        r'ANEX[O0]\s*[_\-\s]*1(?!\d)',
    ]
    for p in patrones_anexo1:
        match = re.search(p, nombre_upper)
        if match:
            # print(f"DEBUG: Match ANEXO 1 pattern '{p}': {match.group(0)}")
            return True, 'ANEXO_1'
            
    # Explicit backup
    n_limpio = nombre_upper.replace(' ', '').replace('_', '').replace('-', '').replace('(', '').replace(')', '')
    if 'ANEXO1' in n_limpio or 'ANEXO01' in n_limpio:
        return True, 'ANEXO_1'

    return False, 'INVALIDO'

def buscar_hoja_servicios_inteligente(hojas: list):
    # (Simplified for debug)
    hojas_norm = {h: h.upper().strip() for h in hojas}
    print(f"DEBUG: Hojas normalizadas: {list(hojas_norm.values())}")
    
    # 6. ANEXO 1 (Regex)
    patrones = [r'ANEXO\s*[_\-\s]*0?1', r'^0?1$']
    for val in hojas_norm.values():
        for p in patrones:
            if re.search(p, val): return val, "Found by Regex ANEXO 1"
            
    # 7. TARIFAS
    for val in hojas_norm.values():
         if 'TARIFAS' in val or 'TARIFA' in val: return val, "Found by TARIFAS generic"
         
    return None, "Not Found"

# ==========================================
# TEST
# ==========================================

archivo = "ACT1-ANEXO 1-0531-2024-HABITALSALUD.xlsb"
full_path = r"c:\Users\daniel.romero\OneDrive - GESTAR INNOVACION S.A.S\Documentos\CONSOLIDADOR POSITIVA\ACT1-ANEXO 1-0531-2024-HABITALSALUD.xlsb"

# print(f"Nombre archivo bytes: {archivo.encode('utf-8')}")

valido, tipo = es_archivo_tarifas_valido(archivo)
print(f"RESULTADO VALIDACION: {valido} ({tipo})")

if os.path.exists(full_path):
    try:
        xls = pd.ExcelFile(full_path, engine='pyxlsb')
        hojas = xls.sheet_names
        print(f"Hojas en archivo: {hojas}")
        sel, reason = buscar_hoja_servicios_inteligente(hojas)
        print(f"Hoja seleccionada: {sel} ({reason})")
    except Exception as e:
        print(f"Error leyendo archivo: {e}")
else:
    print("Archivo no encontrado en disco.")
