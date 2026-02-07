
import re
import sys
import os
import pandas as pd

# Redirigir stdout
sys.stdout = open('debug_531_v5.log', 'w', encoding='utf-8')

# --- DEPENDENCIAS COPIADAS DE CONSOLIDADOR ---

CIUDADES_COLOMBIA_COMPLETA = {'POPAYAN', 'CAUCA'} # Simplificado
DEPARTAMENTOS_COLOMBIA = {'CAUCA'}
PALABRAS_INVALIDAS_CUPS = {'TARIFA', 'CODIGO'}
PREFIJOS_CELULAR_COLOMBIA = {'300', '310', '320'}

def es_telefono_celular(valor: str) -> bool:
    valor_str = str(valor).strip()
    valor_clean = re.sub(r'[^\d]', '', valor_str)
    if len(valor_clean) != 10: return False
    return valor_clean[:3] in PREFIJOS_CELULAR_COLOMBIA

def validar_cups(cups: str, fila: list = None) -> bool:
    # v15.2 Logic
    if not cups: return False
    cups_str = str(cups).strip()
    if cups_str.endswith('.0'): cups_str = cups_str[:-2]
    cups_u = cups_str.upper()

    if not cups_str or len(cups_str) > 15: return False
    if cups_u in CIUDADES_COLOMBIA_COMPLETA: return False
    if cups_u in DEPARTAMENTOS_COLOMBIA: return False
    for palabra in PALABRAS_INVALIDAS_CUPS:
        if palabra in cups_u: return False

    cups_digits = re.sub(r'[^\d]', '', cups_str)

    # 🆕 v15.2: Mejora detección de valores monetarios
    if cups_digits and len(cups_digits) >= 10 and cups_digits == cups_str:
        pass 
    elif cups_digits and len(cups_digits) >= 7 and cups_digits != cups_str:
        pass
    elif cups_digits and len(cups_digits) >= 7 and cups_digits == cups_str:
        pass

    if es_telefono_celular(cups_str): return False
    
    # 9. 🆕 v15.2: RECHAZAR si parece código de habilitación (10-12 dígitos puros)
    if cups_digits and cups_digits == cups_str and 10 <= len(cups_digits) <= 12:
        return False

    return True

def normalizar_texto(t):
    if not isinstance(t, str): return str(t) if t is not None else ""
    return t.upper().strip()

def detectar_columnas_simulado(fila: list) -> dict:
    idx = {'cups': -1, 'tarifa': -1, 'descripcion': -1}
    patrones = {
        'cups': ['CODIGO CUPS', 'CÓDIGO CUPS', 'COD CUPS', 'COD. CUPS'],
        'tarifa': ['TARIFA UNITARIA EN PESOS', 'TARIFA UNITARIA PESOS', 'TARIFA', 'VALOR UNITARIO'],
        'descripcion': ['DESCRIPCION', 'DESCRIPCIÓN']
    }
    for i, celda in enumerate(fila):
        t = normalizar_texto(celda)
        for campo, lista in patrones.items():
            if idx[campo] != -1: continue
            for pat in lista:
                if pat in t:
                    idx[campo] = i
                    break
    return idx

def buscar_hoja_servicios_inteligente(hojas: list):
    hojas_norm = {h: h.upper().strip() for h in hojas}
    
    # 6. ANEXO 1
    patrones = [r'ANEXO\s*[_\-\s]*0?1', r'^0?1$']
    for original, normalized in hojas_norm.items():
        for p in patrones:
            if re.search(p, normalized): return original, "Found by Regex ANEXO 1"
            
    # 7. TARIFAS
    for original, normalized in hojas_norm.items():
         if 'TARIFAS' in normalized or 'TARIFA' in normalized: return original, "Found by TARIFAS generic"
         
    return None, "Not Found"

# TEST
path = r"c:\Users\daniel.romero\OneDrive - GESTAR INNOVACION S.A.S\Documentos\CONSOLIDADOR POSITIVA\ACT1-ANEXO 1-0531-2024-HABITALSALUD.xlsb"

print(f"--- ANALISIS V5: {path} ---")

if os.path.exists(path):
    try:
        xls = pd.ExcelFile(path, engine='pyxlsb')
        hojas = xls.sheet_names
        
        sel, method = buscar_hoja_servicios_inteligente(hojas)
        print(f"Hoja Seleccionada: '{sel}' ({method})")
        
        if sel:
            df = pd.read_excel(path, sheet_name=sel, header=None, nrows=20, engine='pyxlsb')
            idx_cols = None
            
            for i, row in df.iterrows():
                fila_lista = row.tolist()
                
                # Check for headers
                cols = detectar_columnas_simulado(fila_lista)
                if cols['cups'] != -1 and cols['tarifa'] != -1:
                    print(f"✅ HEADER ENCONTRADO EN FILA {i}: {cols}")
                    idx_cols = cols
                    continue
                
                # If headers found, check CUPS
                if idx_cols:
                    cups_raw = fila_lista[idx_cols['cups']]
                    if pd.notna(cups_raw):
                        es_valido = validar_cups(str(cups_raw), fila_lista)
                        estado = "VALIDO" if es_valido else "❌ INVALIDO"
                        print(f"  Fila {i}: CUPS='{cups_raw}' -> {estado}")
                    else:
                        print(f"  Fila {i}: CUPS vacío")
                        
    except Exception as e:
        print(f"ERROR: {e}")
