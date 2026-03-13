"""
Módulo de extracción de metadata desde PDFs de Actas de Negociación.

Estrategia de extracción (robusta):
  1. Intenta extracción de texto nativo con pymupdf
  2. Si no hay texto (PDF basado en imagen), usa OCR con pytesseract + pymupdf
  3. Analiza el texto con regex para extraer:
     - Número de acta
     - Checkboxes: Inclusión / Ajuste / Exclusión
     - Fecha "Desde" del periodo de vigencia
"""
import re
import os
import io
import logging
from dataclasses import dataclass
from typing import Optional
from datetime import date

LOG = logging.getLogger(__name__)

# ── Mapa de meses en español ──
MESES = {
    'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
    'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
    'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
}

# ── Ruta de Tesseract en Windows ──
_TESSERACT_PATHS = [
    r'C:\Program Files\Tesseract-OCR\tesseract.exe',
    r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
    os.path.expanduser(r'~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'),
]


@dataclass
class ActaPdfMetadata:
    """Metadata extraída de un PDF de Acta de Negociación."""
    numero_acta: Optional[int] = None
    inclusion: bool = False
    ajuste: bool = False
    exclusion: bool = False
    fecha_desde: Optional[date] = None
    fecha_hasta_texto: Optional[str] = None  # "Próxima Negociación" o fecha


def _extraer_texto_nativo(ruta_pdf: str) -> str:
    """Extrae texto usando pymupdf (rápido, solo funciona si el PDF tiene texto nativo)."""
    import pymupdf
    texto = ""
    try:
        doc = pymupdf.open(ruta_pdf)
        for page in doc:
            texto += (page.get_text() or "") + "\n"
        doc.close()
    except Exception as e:
        LOG.warning(f"Error extrayendo texto nativo de {ruta_pdf}: {e}")
    return texto.strip()


def _extraer_texto_ocr(ruta_pdf: str) -> str:
    """
    Extrae texto usando OCR (pymupdf para renderizar + pytesseract para reconocer).
    Usa procesamiento de imagen (binarización, alto contraste) para mejorar la
    detección de checkboxes en documentos escaneados.
    """
    try:
        import pymupdf
        import pytesseract
        from PIL import Image, ImageEnhance
    except ImportError as e:
        LOG.warning(f"Dependencias OCR no disponibles: {e}")
        return ""

    # Configurar ruta de Tesseract
    for path in _TESSERACT_PATHS:
        if os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break

    texto = ""
    try:
        doc = pymupdf.open(ruta_pdf)
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes('png')))

            # Mejorar contraste y binarizar para mejor detección de checkboxes
            enhancer = ImageEnhance.Contrast(img)
            img_enhanced = enhancer.enhance(2.0)
            img_bw = img_enhanced.convert('L').point(lambda x: 0 if x < 128 else 255)

            texto += pytesseract.image_to_string(img_bw, lang='eng') + "\n"
        doc.close()
    except Exception as e:
        LOG.warning(f"Error OCR en {ruta_pdf}: {e}")
    return texto.strip()


def _parsear_fecha_acta(texto_fecha: str) -> Optional[date]:
    """
    Parsea fechas en formatos variados:
      - '01/JUNIO/2024' o '01 /JUNIO/ 2024'
      - '24/10/2024'
      - '2024/10/24'
    """
    texto_fecha = texto_fecha.strip().replace(' ', '')

    # Formato dd/MES_NOMBRE/yyyy
    m = re.match(r'(\d{1,2})/([A-Za-zÁÉÍÓÚáéíóú]+)/(\d{4})', texto_fecha)
    if m:
        dia = int(m.group(1))
        mes_nombre = m.group(2).upper()
        anio = int(m.group(3))
        mes = MESES.get(mes_nombre)
        if mes:
            try:
                return date(anio, mes, dia)
            except ValueError:
                pass

    # Formato dd/mm/yyyy
    m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', texto_fecha)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    # Formato yyyy/mm/dd
    m = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', texto_fecha)
    if m:
        try:
            return date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            pass

    return None


def _extraer_numero_acta(texto: str) -> Optional[int]:
    """Extrae el número de acta del texto del PDF."""
    patrones = [
        r'ACTA\s*(?:DE\s*)?(?:NEGOCIACI[OÓ]N\s*)?(?:N[OÚº°]?\.?\s*)?#?\s*(\d+)',
        r'Acta\s*#\s*(\d+)',
        r'ACT[_\-\s]?(\d+)',
        r'ASISTENCIAL\s*(?:N[°º]?)?\s*#?\s*(\d+)',
    ]
    for patron in patrones:
        m = re.search(patron, texto)
        if m:
            try:
                return int(m.group(1))
            except (ValueError, IndexError):
                continue
    return None


def _detectar_checkboxes_por_palabras(ruta_pdf: str) -> Optional[dict]:
    """
    Estrategia 0: usa el API de palabras de pymupdf para detectar checkboxes
    gráficos cuyo caracter [X] no aparece en el flujo normal de get_text().

    Busca la página con 'Objeto del acta', obtiene las coordenadas de
    'Inclusión' y 'Ajuste', luego detecta cualquier 'X' (o variante) en
    esa línea y determina a cuál opción pertenece por posición horizontal.

    Retorna dict {'inclusion': bool, 'ajuste': bool} si se pudo determinar,
    o None si la página no tiene el patrón esperado.
    """
    try:
        import pymupdf
    except ImportError:
        return None

    _CHECKBOX_CHARS = {'X', 'x', '\u2713', '\u221a', '\u2714', 'v', 'V'}

    try:
        doc = pymupdf.open(ruta_pdf)
        for page in doc:
            page_text = page.get_text()
            if not re.search(r'[Oo]bjeto\s+del\s+acta', page_text):
                continue

            words = page.get_text('words')
            # Cada elemento: (x0, y0, x1, y1, text, block, line, word)

            # Localizar la línea con "Inclusión" y "Ajuste de Tarifas"
            pos_incl_x = None
            pos_ajuste_x = None
            y_ref = None

            for w in words:
                t = w[4].strip()
                if re.match(r'Inclusi', t, re.IGNORECASE) and pos_incl_x is None:
                    pos_incl_x = w[0]
                    y_ref = w[1]
                if t.upper() == 'AJUSTE' and y_ref is not None and abs(w[1] - y_ref) < 15:
                    pos_ajuste_x = w[0]

            if pos_incl_x is None or pos_ajuste_x is None:
                doc.close()
                return None

            inclusion_checked = False
            ajuste_checked = False

            for w in words:
                t = w[4].strip()
                if t not in _CHECKBOX_CHARS:
                    continue
                # Verificar que esté en la misma línea horizontal que las opciones
                if abs(w[1] - y_ref) > 20:
                    continue
                x = w[0]
                # Si el X está antes de "Ajuste" → pertenece a Inclusión
                if x < pos_ajuste_x:
                    inclusion_checked = True
                else:
                    ajuste_checked = True

            doc.close()
            if inclusion_checked or ajuste_checked:
                LOG.debug(f"Checkboxes por palabras: inclusion={inclusion_checked} ajuste={ajuste_checked}")
                return {'inclusion': inclusion_checked, 'ajuste': ajuste_checked}
            return None

        doc.close()
    except Exception as e:
        LOG.debug(f"Error en deteccion por palabras: {e}")
    return None


def _detectar_checkboxes(texto: str) -> dict:
    """
    Detecta qué checkboxes están marcados en la sección 'Objeto del acta'.

    Estrategias de detección (en orden de prioridad):

    1. Checkbox explícito: [X] o X junto al texto
    2. Checkbox vacío detectado: [ ] indica NO marcado (si la otra opción
       NO tiene [ ], entonces esa otra SÍ está marcada)
    3. Análisis posicional: X suelta entre las opciones
    4. Texto descriptivo: "se realiza la Inclusión de Servicios"
    """
    resultado = {'inclusion': False, 'ajuste': False}

    # Buscar la sección "Objeto del acta" (flexible para OCR)
    # OCR puede producir: "Objeto del acta", "Obdjeto de contrata", "Objeto de! acta", "Objete del acta"
    m_objeto = re.search(r'[Oo]b[dj]?jet[oae]\s+del?[!\s]\s*[Aa]cta', texto, re.IGNORECASE)
    if not m_objeto:
        # Fallback: buscar directamente las opciones de inclusión/ajuste
        # OCR puede producir: "Inclusidn", "Inclusién", "Inclusi6n", "servicics"
        m_objeto = re.search(r'Inclusi[oó\xe9a-z]n\s+de\s+servici', texto, re.IGNORECASE)
    if not m_objeto:
        # Fallback 2: buscar "Ajuste de Tarifas" directamente
        m_objeto = re.search(r'Ajuste\s+de\s+(?:[Tt]arifas|servicios)', texto, re.IGNORECASE)

    # Tomar texto desde el punto encontrado hasta firmas (max 2000 chars)
    # Si no se encontró ancla, usar todo el texto (solo Estrategia 3 será útil)
    if m_objeto:
        bloque = texto[m_objeto.start():m_objeto.start() + 2000]
    else:
        bloque = texto[:2000]
        LOG.debug("No se encontró ancla 'Objeto del acta' ni opciones - usando texto completo para Estrategia 3")

    # NOTA: Todas las estrategias ACUMULAN flags sin retornar temprano.
    # Un ACTA puede ser de inclusión Y ajuste simultáneamente, así que
    # cada estrategia evalúa ambos flags de forma independiente.

    # ── Estrategia 1: Buscar [X] explícito junto a la opción ──
    patrones_inclusion_marcada = [
        r'Inclusi[oó\xe9]n\s+de\s+servicios\s+[^\n]*?\[\s*[Xx\u2713\u221A\u2714]\s*\]',
        r'\[\s*[Xx\u2713\u221A\u2714]\s*\]\s*[^\n]*?Inclusi[oó\xe9]n\s+de\s+servicios',
        r'Inclusi[oó\xe9]n\s+de\s+servicios\s+[Xx](?:\s|$)',
    ]

    patrones_ajuste_marcado = [
        r'Ajuste\s+de\s+(?:[Tt]arifas|servicios)\s+[^\n]*?\[\s*[Xx\u2713\u221A\u2714]\s*\]',
        r'\[\s*[Xx\u2713\u221A\u2714]\s*\]\s*[^\n]*?Ajuste\s+de\s+(?:[Tt]arifas|servicios)',
        r'Ajuste\s+de\s+(?:[Tt]arifas|servicios)\s+[Xx](?:\s|$)',
    ]

    for p in patrones_inclusion_marcada:
        if re.search(p, bloque, re.IGNORECASE):
            resultado['inclusion'] = True
            break

    for p in patrones_ajuste_marcado:
        if re.search(p, bloque, re.IGNORECASE):
            resultado['ajuste'] = True
            break

    # ── Estrategia 2: Detectar checkbox VACÍO [ ] ──
    # En PDFs con OCR, el checkbox lleno no muestra [ ] pero el vacío sí.
    # "1. Inclusion de servicios 2. Ajuste de Tarifas [ ]"
    #   → Ajuste tiene [ ] vacío → NO marcado
    #   → Inclusión NO tiene [ ] → SÍ marcada
    # Patrones de checkbox vacío: [ ], [|, [||, |], CL], C], [J (errores comunes de OCR)
    _VACIO_RE = r'(?:\[\s*\]|\[\|+|\|\]|CL\]|C\]|\[J|\[\s*$)'
    inclusion_vacia = bool(re.search(
        r'Inclusi[oó\xe9]n\s+de\s+servicios\s*' + _VACIO_RE, bloque, re.IGNORECASE | re.MULTILINE
    ))
    ajuste_vacio = bool(re.search(
        r'Ajuste\s+de\s+(?:[Tt]arifas|servicios)\s*' + _VACIO_RE, bloque, re.IGNORECASE | re.MULTILINE
    ))

    if inclusion_vacia or ajuste_vacio:
        tiene_inclusion_texto = bool(re.search(r'Inclusi[oó\xe9]n\s+de\s+servicios', bloque, re.IGNORECASE))
        tiene_ajuste_texto = bool(re.search(r'Ajuste\s+de\s+(?:[Tt]arifas|servicios)', bloque, re.IGNORECASE))
        if tiene_inclusion_texto and not inclusion_vacia:
            resultado['inclusion'] = True
        if tiene_ajuste_texto and not ajuste_vacio:
            resultado['ajuste'] = True

    # ── Estrategia 3: Texto descriptivo ──
    # Buscar frases en el cuerpo del documento que indican el tipo de acta.
    # Se evalúan AMBOS conjuntos de patrones siempre (no retornar con uno solo).
    # Tolerante a errores de OCR: "soperta"→"soporta", "justificacidn"→"justificación"
    _OCR_INCL = r'inclusi[oó\xe9a-z]n'  # inclusión/inclusidn/inclusian
    _OCR_JUST = r'justificaci[oó\xe9a-z]n'  # justificación/justificacidn
    _patrones_inclusion_texto = [
        r'se\s+realiza\s+la\s+(?:presente\s+)?' + _OCR_INCL + r'\s+de\s+(?:servicios?|tarifas?)',
        r'para\s+(?:la\s+)?' + _OCR_INCL + r'\s+de\s+(?:un\s+)?servicios?\s+(?:al|del)\s+contrato',
        _OCR_JUST + r'\s+para\s+(?:la\s+)?' + _OCR_INCL + r'\s+de\s+servicios?',
        r'sop[oe]rta\s+[l\[]\w?\s+[Ss]olicitud[^\n]{0,80}' + _OCR_INCL + r'\s+de\s+servicios?',
        r'se\s+requiere\s+(?:efectuar|realizar)\s+(?:la\s+)?' + _OCR_INCL,
        r'acuerdan\s+(?:la|el|al)\s+' + _OCR_INCL + r'\s+de\s+(?:servicios?|tarifas?)',
        r'para\s+inclu\w+\s+cups',  # OCR: "para incluit cups", "para incluir cups"
        _OCR_INCL + r'\s+de\s+servicios?\s+(?:que\s+en|a\s+tarifa)',  # "Inclusión de servicios que en..."
        _OCR_INCL + r'\s+de\s+tarifas?\s+(?:mediante|de\s+\w+)',  # "inclusión de tarifas mediante/de EPP"
        _OCR_INCL + r'\s+de\s+servicios?\s+(?:al?\s+(?:contrato|tarifa))',
        r'solicitud\s+de\s+' + _OCR_INCL,  # "solicitud de inclusión"
        r'INCLUSI[OÓ]N\s+DE\s+SERVICIOS?\s*$',  # Header suelto "INCLUSION DE SERVICIOS"
    ]
    _patrones_ajuste_texto = [
        r'se\s+realiza\s+(?:el\s+)?(?:presente\s+)?ajuste\s+(?:de\s+)?tarif',
        _OCR_JUST + r'\s+para\s+(?:el\s+)?ajuste\s+(?:de\s+)?tarif',
        r'sop[oe]rta\s+[l\[]\w?\s+[Ss]olicitud[^\n]{0,80}ajuste\s+(?:de\s+)?tarif',
        r'acuerdan\s+(?:el|al)\s+ajuste\s+(?:de\s+)?(?:los\s+)?(?:servicios\s+y\s+)?tarif',
        r'se\s+requiere\s+(?:efectuar|realizar)\s+(?:el\s+)?ajuste',
        r'se\s+efect[uú]a\s+(?:el\s+)?ajuste\s+(?:de\s+)?tarif',
        r'se\s+requiere\s+ajuste\s+tarif',
        r'sop[oe]rta\s+[l\[]\w?\s+[Ss]olicitud[^\n]{0,80}ajuste\s+tarif',  # "ajuste tarifario"
        r'se\s+realiza\s+(?:la\s+)?(?:presente\s+)?actualizaci[oó]n\s+de\s+tarif',  # "se realiza la presente actualización de tarifas"
        r'acuerdan\s+(?:el|al)\s+ajuste\s+de\s+(?:los\s+)?servicios',  # "acuerdan el ajuste de los servicios"
    ]

    if not resultado['inclusion']:
        for p in _patrones_inclusion_texto:
            if re.search(p, texto, re.IGNORECASE | re.MULTILINE):
                resultado['inclusion'] = True
                break

    if not resultado['ajuste']:
        for p in _patrones_ajuste_texto:
            if re.search(p, texto, re.IGNORECASE | re.MULTILINE):
                resultado['ajuste'] = True
                break

    # ── Estrategia 4: Análisis posicional (X suelta / checkbox vacío OCR) ──
    # Solo si aún falta determinar algún flag.
    if not resultado['inclusion'] or not resultado['ajuste']:
        lineas = bloque.split('\n')
        _idx_incl = None
        _idx_ajust = None
        for i, linea in enumerate(lineas):
            linea_upper = linea.upper().strip()
            if 'INCLUSI' in linea_upper and 'AJUSTE' in linea_upper:
                _idx_incl = i
                _idx_ajust = i
                break
            if 'INCLUSI' in linea_upper and 'SERVICIO' in linea_upper and _idx_incl is None:
                _idx_incl = i
            if 'AJUSTE' in linea_upper and ('TARIF' in linea_upper or 'SERVICIO' in linea_upper) and _idx_ajust is None:
                _idx_ajust = i

        if _idx_incl is not None or _idx_ajust is not None:
            _start = min(i for i in [_idx_incl, _idx_ajust] if i is not None)
            contexto = '\n'.join(lineas[_start:])
            contexto_upper = contexto.upper()

            _zona_firmas = len(contexto)
            for _kw_firma in ['NOMBRES Y APELLID', 'FIRMA', 'ELABOR', 'REVIS']:
                _pos_fw = contexto_upper.find(_kw_firma)
                if _pos_fw >= 0 and _pos_fw < _zona_firmas:
                    _zona_firmas = _pos_fw

            pos_incl = contexto_upper.find('INCLUSI')
            pos_ajust = contexto_upper.find('AJUSTE')

            # Checkbox vacío (normal o garbled por OCR): [ ], [|, [||, |], CL], C], [J
            _VACIO_OCR = r'(?:\[\s*\]|\[\|+|\|\]|CL\]|C\]|\[J|\[\s*$)'
            _vacio_incl = bool(re.search(r'INCLUSI[^\n]{0,30}' + _VACIO_OCR, contexto_upper))
            _vacio_ajust = bool(re.search(r'AJUSTE[^\n]{0,30}' + _VACIO_OCR, contexto_upper))

            if _vacio_incl or _vacio_ajust:
                if _vacio_ajust and not _vacio_incl and pos_incl >= 0:
                    resultado['inclusion'] = True
                if _vacio_incl and not _vacio_ajust and pos_ajust >= 0:
                    resultado['ajuste'] = True
            else:
                xs_encontradas = list(re.finditer(r'\bX\b', contexto, re.IGNORECASE))
                if xs_encontradas and pos_incl >= 0 and pos_ajust >= 0:
                    for m_x in xs_encontradas:
                        pos_x = m_x.start()
                        linea_x = contexto[:pos_x].count('\n')
                        if linea_x == 0:
                            continue
                        if pos_x >= _zona_firmas:
                            continue
                        if abs(pos_x - pos_incl) < abs(pos_x - pos_ajust):
                            resultado['inclusion'] = True
                        else:
                            resultado['ajuste'] = True

    return resultado


def _detectar_exclusion(texto: str) -> bool:
    """
    Detecta si el acta es de exclusión.
    Busca la palabra 'exclusión' pero ignora 'excluidos' que es boilerplate.
    """
    texto_upper = texto.upper()

    # Buscar "exclusión" como concepto del acta (no del boilerplate)
    patrones_exclusion = [
        r'EXCLUSI[OÓ]N\s+DE\s+SERVICIOS?',
        r'PARA\s+LA\s+EXCLUSI[OÓ]N',
        r'SE\s+REALIZA\s+(?:LA\s+)?EXCLUSI[OÓ]N',
        r'OBJETO\s+DEL\s+ACTA.*?EXCLUSI[OÓ]N',
    ]

    for patron in patrones_exclusion:
        if re.search(patron, texto_upper, re.DOTALL):
            return True

    return False


def _extraer_fecha_desde(texto: str) -> Optional[date]:
    """Extrae la fecha 'Desde' del periodo de vigencia."""
    patrones = [
        # "Desde: 01 /JUNIO/ 2024" o "Desde: 01/JUNIO/2024"
        r'[Dd]esde[:\s]+(\d{1,2}\s*/\s*[A-Za-zÁÉÍÓÚáéíóú]+\s*/\s*\d{4})',
        # "Desde 24/10/2024"
        r'[Dd]esde[:\s]+(\d{1,2}\s*/\s*\d{1,2}\s*/\s*\d{4})',
        # "Desde: 2024/10/24"
        r'[Dd]esde[:\s]+(\d{4}\s*/\s*\d{1,2}\s*/\s*\d{1,2})',
    ]

    for patron in patrones:
        m = re.search(patron, texto)
        if m:
            fecha = _parsear_fecha_acta(m.group(1))
            if fecha:
                return fecha

    return None


def _extraer_fecha_hasta(texto: str) -> Optional[str]:
    """Extrae el texto 'Hasta' del periodo de vigencia."""
    m = re.search(r'[Hh]asta[:\s]+(.+?)(?:\n|$)', texto)
    if m:
        return m.group(1).strip()
    return None


def extraer_metadata_acta_pdf(ruta_pdf: str) -> ActaPdfMetadata:
    """
    Función principal: extrae metadata de un PDF de Acta de Negociación.

    Estrategia:
      1. Intenta texto nativo (rápido)
      2. Si vacío, usa OCR (más lento pero funciona con imágenes)
      3. Analiza con regex + NLP heurístico
    """
    meta = ActaPdfMetadata()

    if not os.path.exists(ruta_pdf):
        LOG.warning(f"PDF no encontrado: {ruta_pdf}")
        return meta

    # Paso 1: Intentar texto nativo
    texto = _extraer_texto_nativo(ruta_pdf)

    # Paso 1.5: Detectar si el texto nativo es solo metadatos de firma digital
    # (Adobe Sign, DocuSign, etc.) sin contenido real del acta.
    # Estos PDFs tienen el contenido como imágenes y solo el audit trail como texto.
    _es_solo_firma = False
    if len(texto.strip()) >= 50:
        _texto_upper = texto.upper()
        _tiene_firma_digital = any(kw in _texto_upper for kw in [
            'ADOBE SIGN', 'INFORME DE AUDITOR', 'ID DE TRANSACCI',
            'DOCUSIGN', 'FIRMADO ELECTR', 'DOCUMENTO COMPLETADO',
        ])
        _tiene_contenido_acta = any(kw in _texto_upper for kw in [
            'OBJETO DEL ACTA', 'PERIODO DE VIGENCIA',
            'INCLUSI' + '\u00d3' + 'N DE SERVICIO',  # INCLUSIÓN DE SERVICIO
            'AJUSTE DE TARIF', 'RED ASISTENCIAL',
            'VICEPRESIDENCIA T',  # "Vicepresidencia técnica"
        ])
        if _tiene_firma_digital and not _tiene_contenido_acta:
            _es_solo_firma = True
            print(f"   PDF con solo firma digital (Adobe Sign), forzando OCR: {os.path.basename(ruta_pdf)}")

    # Paso 2: Si no hay texto útil o es solo firma digital, usar OCR
    if len(texto.strip()) < 50 or _es_solo_firma:
        if not _es_solo_firma:
            print(f"   PDF sin texto nativo, usando OCR: {os.path.basename(ruta_pdf)}")
        texto = _extraer_texto_ocr(ruta_pdf)

    if not texto or len(texto.strip()) < 50:
        LOG.warning(f"No se pudo extraer texto de {ruta_pdf}")
        return meta

    # Paso 2.5: Validar que el contenido sea de un acta de negociación
    texto_upper = texto.upper()
    _es_acta = any(kw in texto_upper for kw in [
        'OBJETO DEL ACTA', 'OBJETO DE', 'ACTA DE NEGOCIACI', 'ACTA DE NEGOCIAGI',
        'INCLUSI', 'AJUSTE DE TARIFA', 'AJUSTE DE SERVICIO',
        'PERIODO DE VIGENCIA', 'EXCLUSI',
        'RED ASISTENCIAL',
    ])
    if not _es_acta:
        return meta

    # Debug: mostrar fragmento del texto extraído para diagnóstico
    _primeras_lineas = '\n'.join(texto.split('\n')[:30])
    print(f"   [PDF DEBUG] Texto extraído ({len(texto)} chars), primeras líneas:")
    for _l in texto.split('\n')[:15]:
        _l_strip = _l.strip()
        if _l_strip:
            print(f"     | {_l_strip[:120]}")

    # Paso 3: Extraer información
    meta.numero_acta = _extraer_numero_acta(texto)

    # Estrategia 0: detección por coordenadas de palabras (más precisa para
    # PDFs con checkboxes gráficos que no aparecen en el texto extraído).
    _cb_palabras = _detectar_checkboxes_por_palabras(ruta_pdf)
    if _cb_palabras is not None:
        meta.inclusion = _cb_palabras['inclusion']
        meta.ajuste = _cb_palabras['ajuste']
        print(f"   [PDF DEBUG] Checkboxes por palabras: inclusion={meta.inclusion} ajuste={meta.ajuste}")
    else:
        checkboxes = _detectar_checkboxes(texto)
        meta.inclusion = checkboxes['inclusion']
        meta.ajuste = checkboxes['ajuste']

    meta.exclusion = _detectar_exclusion(texto)

    meta.fecha_desde = _extraer_fecha_desde(texto)
    meta.fecha_hasta_texto = _extraer_fecha_hasta(texto)

    # Debug: resultado
    print(f"   [PDF DEBUG] Resultado: inclusion={meta.inclusion} ajuste={meta.ajuste} exclusion={meta.exclusion} desde={meta.fecha_desde}")

    return meta
