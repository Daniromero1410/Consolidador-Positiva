
import sys
import os

# Agregamos el directorio actual al path para importar el módulo
sys.path.append(os.getcwd())

# Importamos las funciones necesarias del script principal
from consolidador_t25_parametrizado import es_archivo_tarifas_valido, validar_cups, es_telefono_celular, es_telefono_celular_colombiano

def test_nombres_archivos():
    print("\n--- TEST VALIDACIÓN NOMBRES DE ARCHIVO ---")
    archivos = [
        "OT1-ANEXO 1-0572-2023-HOSPITAL DEPARTAMENTAL DE VILLAVICENCIO.xlsb",
        "0526-2021-ANEXO_1-E.S.E HOSPITAL LA DIVINA MISERICORDIA.xlsb", # Fixed spacing slightly
        "0526-2021\t0526-2021-ANEXO_1-E.S.E HOSPITAL LA DIVINA MISERICORDIA.xlsb", # Original with tab
        # Casos que deberían ser válidos según la lógica actual pero verificamos
        "ANEXO 1 CONTRATO 123.xlsx",
        "OTROSI 1 AL CONTRATO.xlsx", 
        "TARIFAS 2024.xlsx",
        # Casos inválidos
        "ANEXO 2 TÉCNICO.xlsx",
        "ANALISIS DE TARIFAS.xlsx",
        # Contratos mencionados por el usuario (no son nombres de archivo validos per se, pero veamos si contienen patrones)
        "531-2024",
        "635-2024",
        "371-2024",
        "215-2024",
        "214-2024",
        "623-2025",
        "464-2025"
    ]

    for nombre in archivos:
        valido, tipo = es_archivo_tarifas_valido(nombre)
        print(f"Arch: '{nombre}' -> Valido: {valido}, Tipo: {tipo}")

def test_cups():
    print("\n--- TEST VALIDACIÓN CUPS ---")
    cups_lista = [
        "123456-01",   # El caso específico del usuario
        "123456",      # CUPS numérico simple
        "ABC123",      # CUPS alfanumérico
        "12345678",    # 8 dígitos (¿Confundido con habilitación?)
        "1234567890",  # 10 dígitos (¿Habilitación? ¿Celular?)
        "3001234567",  # Celular explícito
        "7614708225",  # Código habilitación ejemplo del código
        "900156-01",   # Otro con guion
        "01234567",    # 8 digitos con cero a la izq
        "OT1-ANEXO",   # Nombre de archivo como CUPS (solo para probar)
    ]
    
    import re

    for cups in cups_lista:
        cups_str = str(cups).strip()
        es_valido = validar_cups(cups)
        status = "OK" if es_valido else "RECHAZADO"
        reason = ""
        
        # Replicamos lógica de rechazo para diagnóstico
        cups_digits = re.sub(r'[^\d]', '', cups_str)
        
        if not es_valido:
            if len(cups_str) > 15: reason += "Longitud > 15; "
            if es_telefono_celular(cups_str): reason += "Celular; "
            if cups_digits and cups_digits == cups_str and 8 <= len(cups_digits) <= 12: reason += "Habilitación (8-12 digitos); "
            if cups_digits and len(cups_digits) >= 7 and cups_digits == cups_str: reason += "Monetario (>=7 digitos); "
            if not reason: reason = "Otro motivo"
            
        print(f"CUPS: '{cups}' -> {status} ({reason})")


if __name__ == "__main__":
    test_nombres_archivos()
    test_cups()
