# Beli Bryag — memoria de decisiones (v01)

Documento: `beli_bryag_v01.pdf`, 16 páginas de 320 × 200 mm para pantalla, 19,5 MB. Programa aprobado: `programa_v01.md`. Contenido: `contenido_v01.md` (original) y `contenido_v02.json` (con las correcciones aprobadas). Fuente: `beli_bryag.typ` + `contenido.typ`.

## Aprobaciones del autor (2026-11-03)

| Puerta | Decisión |
|---|---|
| Encargo | Texto de `Beli Bryag.pdf` («tajo de carbón»); fotos con los recortes de la maqueta anterior; PDF para pantalla; firma «Jesús Ramos Martín, 2025» |
| Correcciones | Grupo A completo; B1 «abandoné»; B2 «apelar a»; B3 «les notificaron»; D1, D3, D4 y D5. **No** aplicadas: B4, B5, B6, C (comas) ni D2 (se mantienen las comillas “ ”) |
| Programa (puerta 1) | Aprobado |
| Muestra (puerta 2) | Estructura aprobada. Probé IBM Plex (muestra v02) y el autor se quedó con la muestra v01 en Spectral. Firma bajo el titular |
| Documento completo (puerta 3) | Aprobado (2026-11-08) |

## Decisiones y su porqué

**Formato: 320 × 200 mm, una página por pantalla.**
- Qué pide el material: se va a ver en pantalla y el original ya funcionaba por pliegos.
- Proceso: las imágenes y el uso mandan sobre el formato `[BRI-ETS-619, TSC-FOB-001]`. 16:10 es el formato del portátil y 5:8 es un intervalo de Bringhurst `[BRI-ETS-645]`.
- Descartado: A4 en pliegos, que obliga a leer dos páginas pequeñas en la pantalla.

**Retícula: 12 × 8 sobre una línea base de 15 pt.**
- Qué pide el material: hay recortes de proporción muy distinta (0,66–1,71), y 12 columnas admiten 2, 3, 4 y 6 divisiones.
- Cada campo va de la línea de mayúsculas de su primera línea a la base de la tercera. Así, el borde superior de las fotos coincide con la mayúscula de la primera línea de texto y el inferior con una base `[MB-GRID-069]`.
- La retícula gobierna las imágenes y el texto entra en rejilla en su primera línea y entre bloques `[MB-GRID-787]`.

**Columna de texto de 4 columnas (92 mm) en bandera.**
- Con Spectral a 11/15 sale una mediana de 47–52 caracteres por línea en las páginas de texto (control automático).
- Descartado: justificar, que con 50 caracteres en español deja ríos `[BRI-ETS-034]`. También probé el corte de línea «optimizado» y lo descarté, porque en bandera desigualaba más el perfil.

**Escala de las fotos según su papel.**
- **A sangre (a todo el alto de la página):**
  - la apertura (F01, por la izquierda);
  - la apertura de «Transición energética» (F12, por la izquierda, como eco de la portada);
  - el cierre (F16, por la derecha).

  En pantalla no hay corte de guillotina `[MB-GRID-040]`.
- **Retrato del abuelo (F10):** solo en su página, como pausa.
- **Retrato del nieto (F08):** centrado en vertical (filas 2–7), con la cita al lado.
- **Demás fotos:** las verticales, a toda la altura de la mancha; las horizontales y las casi cuadradas, a 6 o 7 filas con el pie debajo.
- **Excepciones declaradas `[BRI-ETS-004]`:**
  - cuando una foto no ocupa un número entero de columnas, manda la altura;
  - F09 se reduce a 180 mm de ancho para dejar 14 mm de aire hasta la columna de texto y para quedar por debajo del retrato de la página anterior.

**Ritmo.**
- El lado de la foto se alterna de una página a otra, y ningún tipo de página se repite más de dos veces seguidas.
- Las páginas de acento (4, 8, 10, 12 y 16) reparten las pausas por todo el documento.

**Pies.**
- Debajo de la foto, con su mismo arranque y una medida de 5 columnas como máximo.
- En las verticales a toda altura, junto a la foto, con la última línea en la base de la mancha `[TSC-FOB-087, MB-GRID-805]`.

**Citas.**
- Spectral Light cursiva a 16/22,5, con la comilla de apertura colgada fuera de la medida `[BRI-ETS-420]`.
- Se distinguen del texto por un solo recurso, la cursiva `[BRI-ETS-066]`.
- Van ancladas a la base de la mancha (págs. 4 y 6), a la base de la foto (pág. 8) o a la cabeza de la mancha (pág. 7).

**Tipografía: una sola familia, Spectral.**
- Titular 36 pt Light, sección 21 pt Light, entradilla 14/20, texto 11/15 con cifras de texto, pie 8,5/11 gris (#5c5c5c) y folio 8 pt.
- El autor la eligió tras comparar 12 opciones (`especimen_tipografia_v01.pdf`, `especimen_tipografia_v02.pdf`, `muestra_v02.pdf`).
- El titular lleva cortes de línea fijados («Beli Bryag: / la incertidumbre / de vivir sobre / un tajo de carbón»). No cambia ninguna palabra: la cadena original se reparte por posiciones.
- La entradilla (14/20) solo entra en la rejilla en su primera línea. Excepción declarada: es un bloque único en la portada, sin columnas vecinas con las que alinearse.

**Orden de lectura del PDF.** Cada página coloca sus elementos en el orden E01…E60, así que el texto se extrae, se copia y lo lee un lector de pantalla en ese orden. Comprobado por programa en las 16 páginas.

**Fotos.**
- Recortes regenerados desde los originales a resolución completa, localizados por correlación con las imágenes del PDF anterior: coincidencia ≥ 0,98 y tono con una diferencia media < 2/255.
- Lado largo de 2400 px, JPEG de calidad 88 y sRGB.
- F13 (lago Rozov) va sin recompresión, porque solo existe a 1619 px.

## Cambios respecto al programa

| Programa | Construido | Motivo |
|---|---|---|
| Firma bajo la entradilla | Firma bajo el titular | Debajo de la entradilla chocaba con el pie de F01; aprobado por el autor |
| Láminas a sangre: F01 y F16 | También F12 (pág. 12) | Revisión: las págs. 10–12 tenían tres verticales casi idénticas seguidas. Con F12 a sangre se marca el paso del pueblo a la política energética |
| Pág. 14: «texto a ambos lados de la foto» | F14 a toda altura a la izquierda; E49 y E52 a la derecha | A los lados de una vertical a toda altura no caben dos columnas de texto de 4 |
| Pág. 6: foto principal a toda altura | F06 a 7 filas, con el pie debajo | Con 1,04, a toda altura invadiría el medianil de la columna de texto |
| Pág. 13: «dos bloques de texto» | E45 y E48 en la columna izquierda, partidos por la foto | Mismo orden de lectura; la horizontal ocupa la derecha |

## Comprobaciones

| Control | Resultado |
|---|---|
| `control_pdf.py` (16 págs., 320 × 200, ≤ 25 MB, fuentes Spectral) | 9 ok y 1 fallo de medida, explicado en la incidencia I-01 |
| Texto del PDF frente a `contenido_v02.json` | Los 44 elementos de texto están, palabra por palabra y en su página. Solo sobran la firma y los folios |
| Cambios de texto frente al original | 24 diferencias, todas de la lista aprobada (A, B1–B3, D1, D4 y D5; D3 es solo cursiva) |
| Fotos | 16, en orden, con la proporción de sus archivos (diferencia < 0,003) y sin texto encima |
| Orden de flujo del PDF | E01…E60 en todas las páginas |
| Render PNG y hojas de contactos | `qa/v01_pNN.png`, `qa/v01_qa_pNN.png` (capa de retícula) y `qa/hojas/beli_bryag_v01-contactos-0N.png` |
| Revisión independiente (revisor externo, solo lectura) | 20 incidencias. Las he resuelto todas, salvo las que el propio revisor recomienda mantener (ver el informe) |
| Antipatrones (§3) | Ninguno presente. El 14 (recorte) no aplica: son los recortes manuales aprobados por el autor y no se recortan de nuevo |

**No comprobado.** Color en pantallas no calibradas. Aspecto impreso: el documento es para pantalla. Si se imprimiera, F13 quedaría a unos 230 ppp.

## Informe de incidencias

| Id | Severidad | Ubicación | Antes | Después | Motivo |
|---|---|---|---|---|---|
| I-01 | Baja (declarada) | Págs. 6, 7, 8 y 11 | El control marca 4 bloques por debajo de 40 cpl | Se mantienen | Son tres citas de 16 pt y un pie de 8,5 pt, no prosa corrida. La regla de 40–85 cpl es para lectura continua |
| I-02 | Alta → resuelta | Pág. 1 | Titular con «la» al final de línea y «carbón» solo en la última | Cortes fijados en 4 líneas equilibradas | Viuda y artículo separado de su nombre |
| I-03 | Alta → resuelta | Pág. 7 | Pie a 70 mm de su foto | Pie en las columnas 4–5, junto a la foto | Pie desconectado |
| I-04 | Alta → resuelta | Pág. 14 | F14 pequeña (5 × 7) y página vacía | F14 a toda altura, con el pie junto a ella | La página se leía como un hueco |
| I-05 | Alta → resuelta | Págs. 10–12 | Tres verticales iguales seguidas | F12 a sangre | Monotonía |
| I-06 | Media → resuelta | Pág. 8 | Banda vacía de 37 mm bajo el retrato | Retrato centrado en vertical (filas 2–7) | Que el blanco se lea como pausa y no como hueco |
| I-07 | Media → resuelta | Pág. 9 | Texto a 5 mm de F09 | F09 a 180 mm de ancho; queda a 14 mm | Texto pegado a la foto |
| I-08 | Media → resuelta | Págs. 1–15 | Flujo del PDF fuera del orden de lectura en 9 páginas | Orden E01…E60 | Copiar, buscar y lectores de pantalla |
| I-09 | Media → resuelta | Pág. 7 | Cita 1,2 mm por encima de la foto | Mayúscula de la cita en la cabeza de la mancha | Alineación con la foto |
| I-10 | Media → resuelta | Pág. 4 | Cita fuera de rejilla | Anclada a la base de la mancha | Coherencia con la pág. 6 |
| I-11 | Media → resuelta | Págs. 10 y 12 | Pies con viuda | Medida de 3 y 4 columnas | Viudas |
| I-12 | Media → resuelta | Págs. 2, 13, 14 y 15 | Párrafo que sigue a una foto sin sangría | Con sangría de 1 em | Coherencia de párrafo |
| I-13 | Baja, se mantiene | Pág. 10 | F10 a 3 mm del centro de la página | Sin cambios | Va sobre la retícula (columna 4) y la compensa el pie de la derecha |
| I-14 | Baja, se mantiene | Todas | Pies a 8,5 pt | Sin cambios | Es el tamaño de la muestra aprobada; en tableta conviene ampliar con el zoom |
