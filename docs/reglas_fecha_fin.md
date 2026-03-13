# Reglas de Fechas - Consolidador POSITIVA

## Reglas de fecha_inicio

Estas reglas definen qué valor toma `fecha_inicio` en los registros de cada tipo de documento.

| Tipo de documento | fecha_inicio | Fuente |
|---|---|---|
| ANEXO INICIAL | Maestra / Fecha inicial | Columna de fecha inicial en la maestra |
| OTROSÍ N | Maestra / Fecha inicial otrosí N | Columna del otrosí N en la maestra (busca por número) |
| ACTA (inclusión) | Fecha del PDF (período de vigencia - "Desde") | Extraída del PDF del acta |
| ACTA (ajuste) | Fecha del PDF (período de vigencia - "Desde") | Extraída del PDF del acta |
| ACTA (exclusión) | Fecha del PDF (período de vigencia - "Desde") | Extraída del PDF del acta |

> **Nota:** Para todas las ACTAs (sin importar el tipo), la fecha_inicio siempre se toma del PDF, del campo que está debajo del texto "período de vigencia de la tarifa".

---

## Reglas de fecha_fin

### Parte A: fecha_fin del registro PROPIO (la fila que se escribe)

Estas reglas definen qué valor toma `fecha_fin` en los registros del documento que se está procesando.

| Tipo de documento | fecha_fin del registro |
|---|---|
| ANEXO INICIAL | Maestra / Fecha fin de vigencias |
| OTROSI N | Maestra / Fecha fin de vigencias |
| ACTA inclusión | Maestra / Fecha fin de vigencias |
| ACTA ajuste | Maestra / Fecha fin de vigencias |
| ACTA exclusión | Fecha del PDF (período de vigencia de la tarifa) |

### Ejemplo Parte A:

Maestra dice: `Fecha fin de vigencias = 31/12/2025`
PDF del ACTA 3 (exclusión) dice: `Período de vigencia desde = 15/03/2025`

| Registro | tipo | fecha_fin |
|---|---|---|
| CUPS 890101 (ANEXO INICIAL) | ANEXO INICIAL | 31/12/2025 |
| CUPS 890101 (OTROSI 1) | OTROSI 1 | 31/12/2025 |
| CUPS 890501 (ACTA 1 - inclusión) | ACTA 1 | 31/12/2025 |
| CUPS 890101 (ACTA 2 - ajuste) | ACTA 2 | 31/12/2025 |
| CUPS 890101 (ACTA 3 - exclusión) | ACTA 3 | 15/03/2025 (del PDF) |

---

## Parte B: Cómo un documento NUEVO afecta la fecha_fin de registros ANTERIORES

Cada contrato tiene un **documento base**: el ANEXO INICIAL o el último OTROSÍ procesado. Además, se mantiene un registro de todas las ACTAs procesadas para el contrato.

```
Documento base: ANEXO INICIAL (o último OTROSÍ si existe)
ACTAs registradas: lista de ACTAs procesadas entre el último doc base y el documento actual
```

### Regla B1: OTROSÍ cierra el predecesor Y las ACTAs intermedias

> "Si se agrega otro sí por ajuste de tarifas se cierra toda las fechas fin de tarifa que se encuentran en el contrato inicial / otrosí anterior, restándole un día a la fecha inicio del otrosí agregado."

- **B1a**: Cierra **TODOS** los CUPS del predecesor (ANEXO INICIAL o OTROSÍ anterior)
- **B1b**: Cierra **TODOS** los CUPS de todas las ACTAs intermedias (las que están entre el predecesor y este OTROSÍ)
- Nueva fecha_fin: `fecha_inicio_otrosi - 1 día`
- cups: `None` (todos)
- Después de aplicar, se limpia la lista de ACTAs intermedias

### Regla B2: ACTA inclusión NO cierra nada

> "Si se agrega un acta por inclusión de servicios debe mantener la fecha fin de tarifas."

- No modifica fecha_fin de ningún registro anterior
- Se registra en la lista de ACTAs (para que documentos futuros puedan cerrarla)

### Regla B3: ACTA exclusión cierra CUPS coincidentes del documento base Y de ACTAs previas

> "Si se agrega un acta por exclusión de servicios se debe cerrar la fecha fin de tarifas restándole un día a la fecha de inicio del acta. Se debe comparar los códigos del acta con los relacionados en el contrato inicial / otrosí."

- **B3a**: Cierra CUPS coincidentes del **documento base** (ANEXO INICIAL o último OTROSÍ)
- **B3b**: Cierra CUPS coincidentes de **ACTAs previas** (inclusión, ajuste, exclusión anteriores)
- Nueva fecha_fin: `fecha_desde_PDF - 1 día`
- Se registra en la lista de ACTAs

### Regla B4: ACTA ajuste cierra CUPS coincidentes del documento base Y de ACTAs previas

> "Si se agrega un acta por ajuste de tarifas, se deben comparar los códigos del acta con los relacionados en el contrato inicial / otrosí."

- **B4a**: Cierra CUPS coincidentes del **documento base** (ANEXO INICIAL o último OTROSÍ)
- **B4b**: Cierra CUPS coincidentes de **ACTAs previas** (inclusión, ajuste, exclusión anteriores)
- Nueva fecha_fin: `fecha_desde_PDF - 1 día`
- Se registra en la lista de ACTAs

---

## Columna "cambios"

Cada registro tiene una columna `cambios` que funciona como log de auditoría. Cuando una regla de cierre modifica el `fecha_fin` de un registro, se escribe el motivo:

| Ejemplo de cambios |
|---|
| Cerrado por OTROSI 1 |
| Cerrado por ACTA 2 (exclusión) |
| Cerrado por ACTA 3 (ajuste) |
| *(vacío si no fue modificado)* |

---

## Ejemplo completo

**Contrato 0953-2024**
- Maestra: `Fecha fin de vigencias = 31/12/2025`
- OTROSÍ 1: `fecha_inicio = 01/07/2025`
- ACTA 1 (inclusión): `fecha_desde_PDF = 01/08/2025`, CUPS: 890501
- ACTA 2 (exclusión): `fecha_desde_PDF = 01/09/2025`, CUPS: 890101, 890201
- ACTA 3 (ajuste): `fecha_desde_PDF = 01/10/2025`, CUPS: 890501

**Cadena:** ANEXO INICIAL → OTROSI 1 → ACTA 1 → ACTA 2 → ACTA 3

### Estado inicial (Parte A, antes de reglas Parte B):

| # | tipo | CUPS | fecha_fin (Parte A) | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | 31/12/2025 | |
| 2 | ANEXO INICIAL | 890201 | 31/12/2025 | |
| 3 | ANEXO INICIAL | 890301 | 31/12/2025 | |
| 4 | OTROSI 1 | 890101 | 31/12/2025 | |
| 5 | OTROSI 1 | 890201 | 31/12/2025 | |
| 6 | OTROSI 1 | 890301 | 31/12/2025 | |
| 7 | ACTA 1 (inclusión) | 890501 | 31/12/2025 | |
| 8 | ACTA 2 (exclusión) | 890101 | 01/09/2025 (del PDF) | |
| 9 | ACTA 2 (exclusión) | 890201 | 01/09/2025 (del PDF) | |
| 10 | ACTA 3 (ajuste) | 890501 | 31/12/2025 | |

### Regla B1: OTROSI 1 cierra ANEXO INICIAL

Predecesor inmediato: ANEXO INICIAL
`nueva_fecha_fin = 01/07/2025 - 1 día = 30/06/2025`
Aplica a TODOS los CUPS.

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | **30/06/2025** | Cerrado por OTROSI 1 |
| 2 | ANEXO INICIAL | 890201 | **30/06/2025** | Cerrado por OTROSI 1 |
| 3 | ANEXO INICIAL | 890301 | **30/06/2025** | Cerrado por OTROSI 1 |

### Regla B2: ACTA 1 (inclusión) NO cierra nada

Predecesor inmediato: OTROSI 1
Sin cambios. La inclusión no modifica fecha_fin de ningún registro anterior.

### Regla B3: ACTA 2 (exclusión) cierra CUPS coincidentes

Predecesor inmediato: **ACTA 1** (no el OTROSI, porque ACTA 1 es el anterior en la cadena)
ACTA 2 tiene CUPS {890101, 890201}. Compara con ACTA 1 que tiene {890501}.
**No hay coincidencia** → sin cambios.

Pero si ACTA 2 viniera justo después de OTROSI 1 (sin ACTA 1 de por medio), el predecesor sería OTROSI 1 y sí cerraría 890101 y 890201.

**Escenario alternativo (sin ACTA 1):**

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 4 | OTROSI 1 | 890101 | **31/08/2025** | Cerrado por ACTA 2 (exclusión) |
| 5 | OTROSI 1 | 890201 | **31/08/2025** | Cerrado por ACTA 2 (exclusión) |
| 6 | OTROSI 1 | 890301 | 31/12/2025 | *(sin cambio, CUPS no coincide)* |

### Regla B4: ACTA 3 (ajuste) cierra CUPS coincidentes

Predecesor inmediato: **ACTA 2**
ACTA 3 tiene CUPS {890501}. Compara con ACTA 2 que tiene {890101, 890201}.
**No hay coincidencia** → sin cambios.

Pero si ACTA 3 viniera justo después de ACTA 1, el predecesor sería ACTA 1 (que tiene 890501) y sí cerraría:

**Escenario alternativo (ACTA 3 después de ACTA 1):**

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 7 | ACTA 1 (inclusión) | 890501 | **30/09/2025** | Cerrado por ACTA 3 (ajuste) |

### Estado FINAL (con la cadena completa original):

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | 30/06/2025 | Cerrado por OTROSI 1 |
| 2 | ANEXO INICIAL | 890201 | 30/06/2025 | Cerrado por OTROSI 1 |
| 3 | ANEXO INICIAL | 890301 | 30/06/2025 | Cerrado por OTROSI 1 |
| 4 | OTROSI 1 | 890101 | 31/12/2025 | |
| 5 | OTROSI 1 | 890201 | 31/12/2025 | |
| 6 | OTROSI 1 | 890301 | 31/12/2025 | |
| 7 | ACTA 1 (inclusión) | 890501 | 31/12/2025 | |
| 8 | ACTA 2 (exclusión) | 890101 | 01/09/2025 | |
| 9 | ACTA 2 (exclusión) | 890201 | 01/09/2025 | |
| 10 | ACTA 3 (ajuste) | 890501 | 31/12/2025 | |

> **Nota:** En este ejemplo solo el OTROSI 1 genera cierre (sobre ANEXO INICIAL). Las ACTAs 2 y 3 no cierran nada porque sus CUPS no coinciden con los del predecesor inmediato en la cadena.

---

## Caso específico: ANEXO INICIAL como base (sin OTROSÍ)

Cuando no hay OTROSÍ, las ACTAs se agregan directamente al ANEXO INICIAL.

**Reglas del ANEXO INICIAL:**
- fecha_fin por defecto: `Maestra / Fecha fin de vigencias`
- OTROSÍ → cierra TODOS los CUPS del ANEXO INICIAL (`fecha_inicio_otrosi - 1 día`)
- ACTA inclusión → mantiene la fecha_fin del ANEXO INICIAL
- ACTA exclusión → cierra CUPS coincidentes del ANEXO INICIAL (`fecha_desde_PDF - 1 día`)
- ACTA ajuste → cierra CUPS coincidentes del ANEXO INICIAL (`fecha_desde_PDF - 1 día`)

### Ejemplo: ANEXO INICIAL con inclusión y luego exclusión

**Contrato 0500-2024**
- Maestra: `Fecha fin de vigencias = 31/12/2025`
- ACTA 1 (inclusión): `fecha_desde_PDF = 01/03/2025`, CUPS: 890501
- ACTA 2 (exclusión): `fecha_desde_PDF = 01/06/2025`, CUPS: 890101, 890201

**Cadena:** ANEXO INICIAL → ACTA 1 → ACTA 2

#### Estado inicial (Parte A):

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | 31/12/2025 | |
| 2 | ANEXO INICIAL | 890201 | 31/12/2025 | |
| 3 | ANEXO INICIAL | 890301 | 31/12/2025 | |
| 4 | ACTA 1 (inclusión) | 890501 | 31/12/2025 | |
| 5 | ACTA 2 (exclusión) | 890101 | 01/06/2025 (del PDF) | |
| 6 | ACTA 2 (exclusión) | 890201 | 01/06/2025 (del PDF) | |

#### Aplicando reglas Parte B:

**ACTA 1 (inclusión):** Documento base = ANEXO INICIAL → NO cierra nada.

**ACTA 2 (exclusión):** Documento base = **ANEXO INICIAL** (no ACTA 1, porque las ACTAs siempre comparan contra el documento base).
ACTA 2 tiene CUPS {890101, 890201}. Compara con ANEXO INICIAL → coinciden 890101 y 890201.
`nueva_fecha_fin = 01/06/2025 - 1 día = 31/05/2025`

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | **31/05/2025** | Cerrado por ACTA 2 (exclusión) |
| 2 | ANEXO INICIAL | 890201 | **31/05/2025** | Cerrado por ACTA 2 (exclusión) |
| 3 | ANEXO INICIAL | 890301 | 31/12/2025 | *(sin cambio, CUPS no coincide)* |

#### Estado FINAL:

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | **31/05/2025** | Cerrado por ACTA 2 (exclusión) |
| 2 | ANEXO INICIAL | 890201 | **31/05/2025** | Cerrado por ACTA 2 (exclusión) |
| 3 | ANEXO INICIAL | 890301 | 31/12/2025 | |
| 4 | ACTA 1 (inclusión) | 890501 | 31/12/2025 | |
| 5 | ACTA 2 (exclusión) | 890101 | 01/06/2025 | |
| 6 | ACTA 2 (exclusión) | 890201 | 01/06/2025 | |

> **Nota:** Las ACTAs siempre comparan contra el **documento base** (ANEXO INICIAL o último OTROSÍ), NO contra otras ACTAs. El documento base solo se actualiza cuando llega un ANEXO INICIAL o un OTROSÍ.

### Ejemplo: ACTA exclusión directamente después del ANEXO INICIAL

**Contrato 0600-2024**
- Maestra: `Fecha fin de vigencias = 31/12/2025`
- ACTA 1 (exclusión): `fecha_desde_PDF = 01/06/2025`, CUPS: 890101

**Cadena:** ANEXO INICIAL → ACTA 1

#### Estado inicial (Parte A):

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | 31/12/2025 | |
| 2 | ANEXO INICIAL | 890201 | 31/12/2025 | |
| 3 | ACTA 1 (exclusión) | 890101 | 01/06/2025 (del PDF) | |

#### Aplicando reglas Parte B:

**ACTA 1 (exclusión):** Predecesor = ANEXO INICIAL (el inmediato anterior).
ACTA 1 tiene CUPS {890101}. Compara con ANEXO INICIAL → coincide 890101.
`nueva_fecha_fin = 01/06/2025 - 1 día = 31/05/2025`

#### Estado FINAL:

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | **31/05/2025** | Cerrado por ACTA 1 (exclusión) |
| 2 | ANEXO INICIAL | 890201 | 31/12/2025 | |
| 3 | ACTA 1 (exclusión) | 890101 | 01/06/2025 | |

---

## Parte C: Orden cronológico de cierres

### Implementación

Las reglas de cierre **NO se generan durante el procesamiento** de archivos (porque los archivos pueden venir en cualquier orden del SFTP). En su lugar:

1. **Durante el procesamiento**: se recolectan metadatos de cada documento (tipo, fecha_inicio, CUPS, flags exclusión/ajuste/inclusión)
2. **Después de procesar todos los contratos**: se ordenan los documentos de cada contrato por `fecha_inicio` ascendente
3. **Se recorre la cadena en orden cronológico**: generando reglas de cierre correctas (quién es el documento base, cuáles son las ACTAs previas)
4. **Se aplican las reglas al CSV**: línea a línea, fecha más temprana gana

### Regla fundamental

> **La fecha de cierre más temprana gana.** Cuando múltiples reglas de cierre aplican al mismo CUPS de un mismo tipo de documento, se aplica la que tenga la `nueva_fecha_fin` más temprana. Las reglas con fecha posterior NO sobreescriben cierres anteriores.

Esto es importante cuando un contrato tiene ACTAs (ajuste/exclusión) que cierran CUPS **antes** de que llegue un OTROSÍ. El OTROSÍ cierra TODOS los CUPS (`cups=None`), pero si un CUPS ya fue cerrado por un ACTA con fecha más temprana, esa fecha se preserva.

### Ejemplo: Cadena con ACTAs y OTROSÍ (orden cronológico)

**Contrato 0953-2024**
- Maestra: `Fecha fin de vigencias = 31/12/2025`
- ANEXO INICIAL: `fecha_inicio = 27/12/2023`, CUPS: 890101, 890201, 890301, 890401
- ACTA 1 (ajuste): `fecha_desde_PDF = 04/04/2024`, CUPS: 890101, 890201
- ACTA 2 (exclusión): `fecha_desde_PDF = 30/04/2024`, CUPS: 890301
- OTROSÍ 1: `fecha_inicio = 19/11/2025`, CUPS: 890101, 890201, 890301, 890401

**Cadena:** ANEXO INICIAL → ACTA 1 → ACTA 2 → OTROSÍ 1

#### Estado inicial (Parte A):

| # | tipo | CUPS | fecha_fin (Parte A) | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | 31/12/2025 | |
| 2 | ANEXO INICIAL | 890201 | 31/12/2025 | |
| 3 | ANEXO INICIAL | 890301 | 31/12/2025 | |
| 4 | ANEXO INICIAL | 890401 | 31/12/2025 | |
| 5 | ACTA 1 (ajuste) | 890101 | 31/12/2025 | |
| 6 | ACTA 1 (ajuste) | 890201 | 31/12/2025 | |
| 7 | ACTA 2 (exclusión) | 890301 | 30/04/2024 (del PDF) | |
| 8 | OTROSI 1 | 890101 | 31/12/2025 | |
| 9 | OTROSI 1 | 890201 | 31/12/2025 | |
| 10 | OTROSI 1 | 890301 | 31/12/2025 | |
| 11 | OTROSI 1 | 890401 | 31/12/2025 | |

#### Reglas de cierre generadas (Parte B):

| Regla | Origen | Afecta | CUPS | nueva_fecha_fin |
|---|---|---|---|---|
| R1 | ACTA 1 (ajuste) | ANEXO INICIAL | {890101, 890201} | 03/04/2024 |
| R2 | ACTA 2 (exclusión) | ANEXO INICIAL | {890301} | 29/04/2024 |
| R3 | OTROSI 1 | ANEXO INICIAL | TODOS | 18/11/2025 |

#### Aplicando reglas (fecha más temprana gana):

**CUPS 890101** → R1 (03/04/2024) y R3 (18/11/2025) aplican → **gana R1** (03/04/2024)
**CUPS 890201** → R1 (03/04/2024) y R3 (18/11/2025) aplican → **gana R1** (03/04/2024)
**CUPS 890301** → R2 (29/04/2024) y R3 (18/11/2025) aplican → **gana R2** (29/04/2024)
**CUPS 890401** → Solo R3 (18/11/2025) aplica → **R3** (18/11/2025)

#### Estado FINAL:

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | **03/04/2024** | Cerrado por ACTA 1 (ajuste) |
| 2 | ANEXO INICIAL | 890201 | **03/04/2024** | Cerrado por ACTA 1 (ajuste) |
| 3 | ANEXO INICIAL | 890301 | **29/04/2024** | Cerrado por ACTA 2 (exclusión) |
| 4 | ANEXO INICIAL | 890401 | **18/11/2025** | Cerrado por OTROSI 1 |
| 5 | ACTA 1 (ajuste) | 890101 | 31/12/2025 | |
| 6 | ACTA 1 (ajuste) | 890201 | 31/12/2025 | |
| 7 | ACTA 2 (exclusión) | 890301 | 30/04/2024 | |
| 8 | OTROSI 1 | 890101 | 31/12/2025 | |
| 9 | OTROSI 1 | 890201 | 31/12/2025 | |
| 10 | OTROSI 1 | 890301 | 31/12/2025 | |
| 11 | OTROSI 1 | 890401 | 31/12/2025 | |

> **Nota:** El OTROSÍ 1 genera regla `cups=None` (cierra TODOS), pero como 890101, 890201 y 890301 ya tenían cierres con fechas más tempranas (de las ACTAs), esos se preservan. Solo 890401, que no fue cerrado por ningún ACTA, recibe la fecha del OTROSÍ.

### Ejemplo: ACTA cierra ACTA previa + OTROSÍ cierra ACTAs intermedias

**Contrato 0700-2024**
- Maestra: `Fecha fin de vigencias = 31/12/2025`
- ANEXO INICIAL: `fecha_inicio = 01/01/2024`, CUPS: 890101, 890201
- ACTA 1 (inclusión): `fecha_desde_PDF = 01/03/2024`, CUPS: 890501
- ACTA 2 (exclusión): `fecha_desde_PDF = 01/06/2024`, CUPS: 890501, 890101
- OTROSÍ 1: `fecha_inicio = 01/11/2024`

**Cadena:** ANEXO INICIAL → ACTA 1 → ACTA 2 → OTROSÍ 1

#### Estado inicial (Parte A):

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | 31/12/2025 | |
| 2 | ANEXO INICIAL | 890201 | 31/12/2025 | |
| 3 | ACTA 1 (inclusión) | 890501 | 31/12/2025 | |
| 4 | ACTA 2 (exclusión) | 890501 | 01/06/2024 (del PDF) | |
| 5 | ACTA 2 (exclusión) | 890101 | 01/06/2024 (del PDF) | |
| 6 | OTROSI 1 | 890101 | 31/12/2025 | |
| 7 | OTROSI 1 | 890201 | 31/12/2025 | |

#### Reglas generadas (Parte B):

**ACTA 1 (inclusión):** No genera regla (B2). Se registra en lista de ACTAs.

**ACTA 2 (exclusión):**
- **B3a**: Cierra CUPS {890501, 890101} del documento base (ANEXO INICIAL) → `fecha_fin = 31/05/2024`
- **B3b**: Cierra CUPS {890501, 890101} de ACTAs previas (ACTA 1) → `fecha_fin = 31/05/2024`
  - ACTA 1 tiene CUPS 890501 → **coincide** → se cierra

**OTROSÍ 1:**
- **B1a**: Cierra TODOS los CUPS de ANEXO INICIAL → `fecha_fin = 31/10/2024`
- **B1b**: Cierra TODOS los CUPS de ACTAs intermedias (ACTA 1, ACTA 2) → `fecha_fin = 31/10/2024`

| Regla | Origen | tipo_afectado | CUPS | nueva_fecha_fin |
|---|---|---|---|---|
| R1 | ACTA 2 (B3a) | ANEXO INICIAL | {890501, 890101} | 31/05/2024 |
| R2 | ACTA 2 (B3b) | ACTA 1 | {890501, 890101} | 31/05/2024 |
| R3 | OTROSI 1 (B1a) | ANEXO INICIAL | TODOS | 31/10/2024 |
| R4 | OTROSI 1 (B1b) | ACTA 1 | TODOS | 31/10/2024 |
| R5 | OTROSI 1 (B1b) | ACTA 2 | TODOS | 31/10/2024 |

#### Aplicando (fecha más temprana gana):

**ANEXO INICIAL 890101**: R1 (31/05/2024) y R3 (31/10/2024) → **gana R1** (31/05/2024)
**ANEXO INICIAL 890201**: Solo R3 (31/10/2024) → **R3** (31/10/2024)
**ACTA 1 890501**: R2 (31/05/2024) y R4 (31/10/2024) → **gana R2** (31/05/2024)
**ACTA 2 890501**: Solo R5 (31/10/2024) → **R5** (31/10/2024)
**ACTA 2 890101**: Solo R5 (31/10/2024) → **R5** (31/10/2024)

#### Estado FINAL:

| # | tipo | CUPS | fecha_fin | cambios |
|---|---|---|---|---|
| 1 | ANEXO INICIAL | 890101 | **31/05/2024** | Cerrado por ACTA 2 (exclusión) |
| 2 | ANEXO INICIAL | 890201 | **31/10/2024** | Cerrado por OTROSI 1 |
| 3 | ACTA 1 (inclusión) | 890501 | **31/05/2024** | Cerrado por ACTA 2 (exclusión) |
| 4 | ACTA 2 (exclusión) | 890501 | **31/10/2024** | Cerrado por OTROSI 1 |
| 5 | ACTA 2 (exclusión) | 890101 | **31/10/2024** | Cerrado por OTROSI 1 |
| 6 | OTROSI 1 | 890101 | 31/12/2025 | |
| 7 | OTROSI 1 | 890201 | 31/12/2025 | |

> **Nota:** Aquí se ven las dos reglas nuevas en acción:
> - **ACTA 2 cierra ACTA 1** (B3b): El CUPS 890501 de ACTA 1 fue cerrado por ACTA 2 porque coincidía.
> - **OTROSÍ 1 cierra ACTAs** (B1b): Los CUPS de ACTA 1 y ACTA 2 fueron cerrados por el OTROSÍ. Pero para ACTA 1 890501, el cierre de ACTA 2 (31/05/2024) era más temprano que el del OTROSÍ (31/10/2024), así que se preservó.
