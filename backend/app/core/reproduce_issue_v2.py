
import re

# ==========================================
# CONSTANTES Y LISTAS (Copiadas del código fuente)
# ==========================================

CIUDADES_COLOMBIA_COMPLETA = {
    # Capitales
    'BOGOTÁ', 'BOGOTA', 'MEDELLÍN', 'MEDELLIN', 'CALI', 'BARRANQUILLA',
    'CARTAGENA', 'BUCARAMANGA', 'CÚCUTA', 'CUCUTA', 'PEREIRA', 'IBAGUÉ',
    'IBAGUE', 'SANTA MARTA', 'MANIZALES', 'VILLAVICENCIO', 'PASTO',
    'MONTERÍA', 'MONTERIA', 'NEIVA', 'ARMENIA', 'SINCELEJO', 'POPAYÁN',
    'POPAYAN', 'VALLEDUPAR', 'TUNJA', 'FLORENCIA', 'QUIBDÓ', 'QUIBDO',
    'RIOHACHA', 'YOPAL', 'MOCOA', 'LETICIA', 'INÍRIDA', 'INIRIDA',
    'MITÚ', 'MITU', 'PUERTO CARREÑO', 'SAN JOSÉ DEL GUAVIARE', 'ARAUCA',
    # Ciudades intermedias usadas en traslados
    'BAHIA SOLANO', 'BARRANCABERMEJA', 'BUENAVENTURA', 'PALMIRA',
    'CARTAGO', 'TULUA', 'TULUÁ', 'BUGA', 'SOGAMOSO', 'DUITAMA', 'GIRARDOT',
    'FUSAGASUGA', 'FUSAGASUGÁ', 'FACATATIVA', 'FACATATIVÁ', 'ZIPAQUIRA',
    'ZIPAQUIRÁ', 'CHIA', 'CHÍA', 'SOACHA', 'RIONEGRO', 'ENVIGADO',
    'ITAGUI', 'ITAGÜÍ', 'BELLO', 'TUMACO', 'IPIALES', 'GRANADA', 'ACACIAS',
    'ACACÍAS', 'PUERTO LOPEZ', 'PUERTO LÓPEZ', 'AGUACHICA', 'OCAÑA',
    'APARTADO', 'APARTADÓ', 'TURBO', 'CAUCASIA', 'MAGANGUE', 'MAGANGUÉ',
    'LORICA', 'CERETE', 'CERETÉ', 'ESPINAL', 'MELGAR', 'FLANDES', 'HONDA',
    'MARIQUITA', 'LA DORADA', 'PUERTO BERRIO', 'PUERTO BERRÍO',
    'PUERTO BOYACA', 'PUERTO BOYACÁ', 'CIENAGA', 'CIÉNAGA', 'FUNDACION',
    'FUNDACIÓN', 'ARACATACA', 'EL BANCO', 'PLATO', 'COROZAL', 'SAMPUES',
    'SAMPUÉS', 'SAN MARCOS', 'ZARZAL', 'JAMUNDI', 'JAMUNDÍ', 'YUMBO',
    'CANDELARIA', 'PRADERA', 'FLORIDA', 'CERRITO', 'GUACARI', 'GUACARÍ',
    'GINEBRA', 'ROLDANILLO', 'LA UNION', 'LA UNIÓN', 'SEVILLA',
    'CAICEDONIA', 'ARGELIA', 'DARIEN', 'DARIÉN', 'RESTREPO', 'DAGUA',
    'LA CUMBRE', 'CLO', 'BOG', 'MDE',  # Códigos de aeropuerto
}

DEPARTAMENTOS_COLOMBIA = {
    'BOGOTÁ D.C', 'BOGOTA D.C', 'BOGOTÁ D.C.', 'BOGOTA D.C.',
    'ANTIOQUIA', 'ATLÁNTICO', 'ATLANTICO', 'BOLÍVAR', 'BOLIVAR',
    'BOYACÁ', 'BOYACA', 'CALDAS', 'CAQUETÁ', 'CAQUETA', 'CASANARE',
    'CAUCA', 'CESAR', 'CHOCÓ', 'CHOCO', 'CÓRDOBA', 'CORDOBA',
    'CUNDINAMARCA', 'GUAINÍA', 'GUAINIA', 'GUAVIARE', 'HUILA',
    'LA GUAJIRA', 'MAGDALENA', 'META', 'NARIÑO', 'NARINO',
    'NORTE DE SANTANDER', 'PUTUMAYO', 'QUINDÍO', 'QUINDIO',
    'RISARALDA', 'SAN ANDRÉS', 'SAN ANDRES', 'SANTANDER', 'SUCRE',
    'TOLIMA', 'VALLE', 'VALLE DEL CAUCA', 'VAUPÉS', 'VAUPES',
    'VICHADA', 'AMAZONAS', 'ARAUCA'
}

PREFIJOS_CELULAR_COLOMBIA = {
    '300', '301', '302', '303', '304', '305',
    '310', '311', '312', '313', '314', '315', '316', '317', '318',
    '320', '321', '322', '323', '324',
    '350', '351',
    '330', '331', '332', '333'
}

PALABRAS_INVALIDAS_CUPS = [
    'CODIGO', 'CUPS', 'ITEM', 'DESCRIPCION', 'TARIFA', 'TOTAL', 'SUBTOTAL',
    'DEPARTAMENTO', 'MUNICIPIO', 'HABILITACION', 'HABIITACION', 'DIRECCION',
    'TELEFONO', 'EMAIL', 'SEDE', 'NOMBRE', 'NUMERO', 'ESPECIALIDAD',
    'MANUAL', 'OBSERV', 'PORCENTAJE', 'HOMOLOGO', 'N°', 'NO.',
    'NOTA', 'NOTAS', 'ACLARATORIA', 'ACLARATORIAS', 'ACLARACION', 'ACLARACIONES',
    'INCLUYE', 'NO INCLUYE', 'EXCLUYE',
    'USO DE EQUIPO', 'DERECHO DE SALA', 'DERECHO SALA',
    'VER NOTA', 'VER NOTAS', 'SEGUN NOTA',
    'APLICA', 'NO APLICA', 'SEGÚN', 'SEGUN',
    'CONSULTAR', 'REVISAR', 'PENDIENTE',
    'VALOR', 'PRECIO', 'COSTO',
    'CONTRATO', 'ACTA', 'OTROSI', 'OTROSÍ',
    'VIGENTE', 'VIGENCIA',
    'TRASLADO', 'ORIGEN', 'DESTINO',
    'TARIFAS PROPIAS', 'TARIFA PROPIA',
]

PATRONES_INVALIDOS_CUPS = [
    r'^\*',
    r'^-+$',
    r'^\d{1,2}$',
    r'^N\.?A\.?$',
    r'^N/A$',
    r'INCLUYE',
    r'NOTA\s*\d*',
]

# ==========================================
# FUNCIONES (Copiadas del código fuente)
# ==========================================

def es_telefono_celular_colombiano(valor: str) -> bool:
    if not valor:
        return False
    valor_str = str(valor).strip()
    if valor_str.endswith('.0'):
        valor_str = valor_str[:-2]
    valor_clean = re.sub(r'[^\d]', '', valor_str)
    if len(valor_clean) != 10:
        return False
    prefijo = valor_clean[:3]
    return prefijo in PREFIJOS_CELULAR_COLOMBIA

def es_telefono_celular(valor: str) -> bool:
    return es_telefono_celular_colombiano(valor)

def es_municipio_o_departamento(texto: str) -> bool:
    if not texto:
        return False
    t = str(texto).upper().strip()
    if t in CIUDADES_COLOMBIA_COMPLETA:
        return True
    if t in DEPARTAMENTOS_COLOMBIA:
        return True
    return False

def es_direccion(texto: str) -> bool:
    # Dummy implementation since I didn't verify the original code for this. It wasn't in the chunks I read carefully.
    # Assuming it checks for CRA, CLA, etc.
    t = str(texto).upper().strip()
    patrones = ['CARRERA', 'CALLE', 'DIAGONAL', 'TRANSVERSAL', 'AVENIDA', 'KM', 'CRA', 'CL', 'DG', 'TV', 'AV']
    for p in patrones:
        if t.startswith(p):
            return True
    return False

def es_numero_sede(texto: str) -> bool:
    # Dummy implementation
    t = str(texto).upper().strip()
    if t.startswith('SEDE'): return True
    return False

def es_dato_de_sede(fila: list) -> bool:
    # Dummy
    return False

def es_fila_de_traslados(fila: list) -> bool:
    if not fila or len(fila) < 3:
        return False
    for i, celda in enumerate(fila[:4]):
        if celda:
            celda_str = str(celda).strip()
            if celda_str.endswith('.0'):
                celda_str = celda_str[:-2]
            celda_upper = celda_str.upper()
            if celda_upper in CIUDADES_COLOMBIA_COMPLETA:
                return True
    return False

def validar_cups(cups: str, fila: list = None) -> bool:
    if not cups:
        return False

    cups_str = str(cups).strip()
    if cups_str.endswith('.0'):
        cups_str = cups_str[:-2]

    cups_u = cups_str.upper()

    # 1. Longitud básica
    if not cups_str or len(cups_str) > 25:
        return False

    # 2. RECHAZAR si es una ciudad
    if cups_u in CIUDADES_COLOMBIA_COMPLETA:
        return False

    # 3. RECHAZAR palabras inválidas
    for palabra in PALABRAS_INVALIDAS_CUPS:
        if palabra in cups_u:
            return False

    # 4. RECHAZAR patrones inválidos
    for patron in PATRONES_INVALIDOS_CUPS:
        if re.search(patron, cups_u):
            return False

    # 5. Extraer solo dígitos
    cups_digits = re.sub(r'[^\d]', '', cups_str)

    # 6. RECHAZAR si parece un valor monetario grande (>= 7 dígitos)
    if cups_digits and len(cups_digits) >= 7:
        if len(cups_digits) == len(cups_str): # Purely numeric
            return False
        # If it has other chars, maybe it's a code? But original code said:
        # if cups_digits and len(cups_digits) >= 7: return False
        # This is quite aggressive.
        return False

    # 7. RECHAZAR si parece teléfono celular
    if es_telefono_celular(cups_str):
        return False

    # 8. RECHAZAR si parece código de habilitación (8-12 dígitos puros)
    if cups_digits and cups_digits == cups_str and 8 <= len(cups_digits) <= 12:
        return False

    # 9. RECHAZAR municipios/departamentos
    if es_municipio_o_departamento(cups_u):
        return False

    # 10. RECHAZAR direcciones
    if es_direccion(cups_u):
        return False

    # 11. RECHAZAR valores especiales
    if cups_u in ['N.A', 'NA', 'N/A', 'N.A.', '-', '--', '---', 'NINGUNO', 'NINGUNA', 'NULL', 'NONE', '']:
        return False

    # 12. RECHAZAR si es número de sede
    if es_numero_sede(cups_str):
        return False

    # 13. Si es solo dígitos, debe tener al menos 4
    if cups_digits and cups_digits == cups_str:
        if len(cups_digits) < 4:
            return False

    # 14. Si la fila completa parece ser de traslados, rechazar
    if fila and es_fila_de_traslados(fila):
        return False

    return True

def es_archivo_tarifas_valido(nombre: str) -> tuple:
    if not nombre: return False, 'INVALIDO'
    nombre_upper = nombre.upper()
    
    palabras_excluir = ['MEDICAMENT', 'MEDICAMENTO', 'MEDICAMENTOS', 'FARMACO', 'FÁRMACO', 'FARMACOS', 'FÁRMACOS', 'INSUMO', 'INSUMOS']
    for palabra in palabras_excluir:
        if palabra in nombre_upper:
            if 'SERVICIO' in nombre_upper or 'SERV' in nombre_upper: continue
            return False, 'INVALIDO'

    if re.search(r'AN[AÁ]LISIS\s*(DE\s*)?(TARIFAS?|TARIFA)', nombre_upper):
        return False, 'INVALIDO'

    patrones_otrosi = [r'OTRO\s*S[IÍ]\s*[_#\-\s]*(\d+)', r'OTROS[IÍ]\s*[_#\-\s]*(\d+)', r'OT[_\-\s]?(\d+)', r'ADICI[OÓ]N\s*[_#\-\s]*(\d+)', r'MODIFICACI[OÓ]N\s*[_#\-\s]*(\d+)']
    for patron in patrones_otrosi:
        if re.search(patron, nombre_upper): return True, 'OTROSI'

    patrones_anexo1 = [r'ANEXO\s*[_\-\s]*0?1(?!\d)', r'ANEX[O0]\s*[_\-\s]*1(?!\d)', r'ANEXO\s*N[OÚº°]?\.?\s*0?1(?!\d)', r'A1[_\-\s]', r'[_\-]ANEXO[_\-]?1', r'ANEXO[_\-]1[_\-]']
    for patron in patrones_anexo1:
        if re.search(patron, nombre_upper): return True, 'ANEXO_1'
    
    n_limpio = nombre_upper.replace(' ', '').replace('_', '').replace('-', '').replace('(', '').replace(')', '')
    if 'ANEXO1' in n_limpio or 'ANEXO01' in n_limpio: return True, 'ANEXO_1'

    patron_anexo_no_1 = r'ANEXO\s*[_\-\s]*([2-9]|[1-9]\d)(?!\d)'
    if re.search(patron_anexo_no_1, nombre_upper): return False, 'INVALIDO'

    patrones_tarifas = [r'\d+[\-_]TARIFAS[\-_]', r'^TARIFAS[\-_]', r'[\-_]TARIFAS[\-_]', r'[\-_]TARIFAS\.']
    for patron in patrones_tarifas:
        if re.search(patron, nombre_upper): return True, 'TARIFAS'

    if 'ANEXO' in nombre_upper and ('TARIFA' in nombre_upper or 'SERV' in nombre_upper):
        otros_anexos = re.search(r'ANEXO\s*[_\-\s]*([2-9]|[1-9]\d)(?!\d)', nombre_upper)
        if not otros_anexos: return True, 'ANEXO_1'

    return False, 'INVALIDO'


# ==========================================
# TEST CORREGIDO
# ==========================================

def run_test():
    print("--- INICIANDO TEST DE REPRODUCCIÓN ---\n")

    # 1. Test Archivos
    archivos = [
        "OT1-ANEXO 1-0572-2023-HOSPITAL DEPARTAMENTAL DE VILLAVICENCIO.xlsb",
        "0526-2021-ANEXO_1-E.S.E HOSPITAL LA DIVINA MISERICORDIA.xlsb",
        "0526-2021\t0526-2021-ANEXO_1-E.S.E HOSPITAL LA DIVINA MISERICORDIA.xlsb"
    ]
    for arch in archivos:
        valido, tipo = es_archivo_tarifas_valido(arch)
        print(f"ARCHIVO: '{arch}'\n   -> Valido: {valido}, Tipo: {tipo}")

    print("\n")

    # 2. Test CUPS
    cups_cases = [
        "123456-01", 
        "12345601",
        "123456",
        "890201",
        "7614708225", # Habilitacion comun
        "12345678", # 8 digitos
    ]
    
    for cups in cups_cases:
        res = validar_cups(cups)
        print(f"CUPS: '{cups}' -> {'✅ OK' if res else '❌ RECHAZADO'}")
        if not res:
            # Diagnose why
            cups_str = str(cups).strip()
            cups_digits = re.sub(r'[^\d]', '', cups_str)
            reasons = []
            if len(cups_digits) >= 7 and len(cups_digits) == len(cups_str): reasons.append("Monetario >= 7 digits")
            elif len(cups_digits) >= 7: reasons.append("Monetario >= 7 digits (with chars?)")
            
            if cups_digits and cups_digits == cups_str and 8 <= len(cups_digits) <= 12: reasons.append("Habilitacion 8-12 digits")
            print(f"   Motivos posibles: {', '.join(reasons)}")

if __name__ == "__main__":
    run_test()

