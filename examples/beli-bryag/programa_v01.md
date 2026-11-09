# Beli Bryag — programa de maquetación (v01)

Estado: **aprobado por el autor (puertas 1 y 2)**. Fecha: 2026-11-03. Los cambios hechos al componer (firma bajo el titular, F12 a sangre, págs. 6, 13 y 14) están en `memoria_v01.md`, en «Cambios respecto al programa».

## 1. Problema

- **Qué es.** Un reportaje fotoperiodístico escrito en primera persona: unas 1.700 palabras, 16 fotografías, una introducción sin rótulo y 4 secciones rotuladas («Beli Bryag», «Sus habitantes», «Transición energética», «Conclusión»), 4 citas de testimonio y 16 pies.
- **Para qué y para quién.** Para enseñar el trabajo del autor (Jesús Ramos Martín) a terceros: editores, salas y conocidos. Se envía como **PDF y se lee en pantalla**, sobre todo en portátil y también en tableta.
- **Restricciones cerradas por el autor.**
  - Texto: versión de `Beli Bryag.pdf` («tajo de carbón»). Solo se corrigen las erratas que apruebe en `erratas_v01.md`.
  - Fotos: las 16 de siempre, en el mismo orden y con el **recorte de la maqueta actual**. Los recortes se regeneran a partir de los originales a resolución completa (ver `contenido_v01.md`).
  - Orden del texto: el de `contenido_v01.md`, elemento a elemento.
  - Firma (paratexto nuevo, aprobado): «Jesús Ramos Martín, 2025». La escribo con las mayúsculas del nombre propio. Confírmalo.
- **Interpretación del orden.** Los 60 elementos de `contenido_v01.md` (texto, fotos, pies y citas) forman una sola secuencia que no se altera. Cada página es un tramo seguido de esa secuencia y, dentro de la página, la composición se lee en ese mismo orden. Así, ninguna foto se adelanta ni se atrasa respecto al texto que la rodeaba.
- **Qué falla en la maqueta actual.** (1) Todas las fotos tienen prácticamente el mismo tamaño y la misma posición: no hay jerarquía ni ritmo, justo lo que Müller-Brockmann señala como error cuando los pesos son distintos `[MB-GRID-008, MB-GRID-076]`. (2) Los bloques de texto están encima o debajo de cada foto, sin retícula común, y dejan huecos distintos en cada página. (3) Dos familias sin relación entre sí (Georgia y Arial Narrow), un pie en cursiva y los demás en redonda, y marcos de texto que saltan de una página a otra del pliego. (4) Está pensada como pliegos A4 impresos, pero se va a ver en pantalla.

**Idea rectora.** Las fotografías llevan el reportaje y el texto las acompaña en una columna estable, como en una revista. Cada página de pantalla es un pliego completo. El ritmo sale de alternar el lado de la foto, las páginas de foto sola (los dos retratos y el cierre) y las páginas apaisadas con cita.

## 2. Programa

### Soporte y formato

- **Página apaisada de 320 × 200 mm (5:8 = 16:10), una por pantalla.** Qué pide el material: se lee en pantalla y la unidad del original ya era el pliego. La proporción 16:10 es la de la mayoría de portátiles, así que la página llena la pantalla sin bandas. 5:8 es además uno de los intervalos que Bringhurst propone como proporción de página `[BRI-ETS-645]`. Que las imágenes manden en el formato es la heurística de `[BRI-ETS-619]`.
- **Descartado:** A4 vertical en pliegos, como el original. Obliga a ver dos páginas a la vez en la pantalla (la letra queda pequeña) o a ver media composición. También descarto el A4 apaisado (1,414), que deja bandas en un portátil.
- **Peso:** objetivo ≤ 20 MB, para poder mandarlo por correo. Fotos en sRGB con 2400 px en el lado largo; a tamaño máximo en página, eso da unos 370 ppp, de sobra para pantalla. Única excepción: F13 (lago Rozov), que solo existe a 1619 × 1080 px y ronda los 200 ppp en su tamaño de página. En pantalla basta; en papel no.

### Retícula

- **Márgenes:** 17 mm a izquierda y derecha, 13 mm arriba y unos 23 mm abajo (el folio va en el margen inferior). Es una página sin lomo, así que los laterales son simétricos. El pie más hondo que la cabeza hace «flotar» la mancha `[MB-GRID-044]`. Mancha de 286 × 164 mm.
- **Línea base de 15 pt** (31 líneas en la mancha). Todo bloque mide un número entero de líneas `[MB-GRID-006, BRI-ETS-055]`.
- **12 columnas con medianil de 5 mm** (columna de 19,25 mm) y **8 filas de 3 líneas** con 1 línea de separación (3 × 8 + 7 = 31). Doce columnas permiten 2, 3, 4 y 6 divisiones, y hacen falta porque los recortes son muy distintos (proporciones de 0,66 a 1,71). Es la combinación de campos que propone Müller-Brockmann para formatos mixtos sin girar nada `[MB-GRID-079, MB-GRID-088]`.
- **Columna de texto de 4 columnas (92 mm), en bandera** a la izquierda. Con Spectral a 11 pt salen unos 54 caracteres por línea, dentro del intervalo de 45–75 de Bringhurst `[BRI-ETS-029]`. Voy a bandera porque justificar 54 caracteres en español deja ríos y particiones, y en pantalla la bandera se lee bien `[BRI-ETS-034, BRI-ETS-035]`. Descartado: texto a dos columnas en toda la página, que relegaría la foto.
- **La retícula gobierna las imágenes y el texto se alinea en su primera y su última línea**, la estrategia de `[MB-GRID-787]` para trabajos en los que mandan las imágenes.

### Imágenes

Ningún tamaño va por defecto: lo fija el papel de cada foto en la secuencia. Hay tres escalas:

| Escala | Dónde | Medida |
|---|---|---|
| **Lámina** | F01 (apertura), F10 (retrato del abuelo), F16 (cierre) | F01 y F16 a sangre a todo el alto de la página (en pantalla no hay corte de guillotina); F10 a toda la altura de la mancha, sola en su página |
| **Principal** | La foto de cada página de texto | Toda la altura de la mancha (164 mm); las horizontales ocupan 6–7 filas para dejar sitio al pie |
| **Con cita** | F04, F08, F09, F13 y F15 | Horizontales que comparten página con una cita o con texto debajo |

- El borde izquierdo o derecho de cada foto cae en una línea de columna, y la base, en la base de la mancha. Como los recortes son fijos, la anchura no siempre coincide con un número entero de columnas. **Excepción declarada:** en ese caso manda la altura `[BRI-ETS-004]`.
- **Pies:** junto a su foto, con su mismo arranque. Van debajo en las horizontales y en la columna vecina, alineados con la base de la foto, en las verticales a toda altura `[TSC-FOB-087, MB-GRID-805]`. Nunca sobre la imagen.
- Sin filetes, marcos, sombras ni fondos de color.

### Tipografía

- **Una sola familia: Spectral** (OFL, archivos estáticos con cursivas verdaderas, versalitas y cifras de texto; Typst la reconoce con ese nombre). Production Type la diseñó para leer en pantalla, que es el soporte de este documento. Tiene un tono de prensa sobria que encaja con un reportaje `[BRI-ETS-001, BRI-ETS-397]`.
- **Descartadas:** Literata (también pensada para pantalla, pero es variable y Typst solo usa su instancia por defecto, así que no se controlan bien los pesos); Newsreader (no tiene versalitas ni cifras de texto); mantener Georgia y Arial (dos familias sin relación entre sí, que es el defecto de la maqueta actual `[TSC-FOB-004]`).
- **Escala** (toda de la serie tradicional `[BRI-ETS-083]`): titular 36 pt Light, sección 21 pt Light, cita 16 pt Light Italic, entradilla 14 pt, texto 11/15 pt, pie 8,5 pt, folio 8 pt. Entre niveles cambia sobre todo el cuerpo `[BRI-ETS-102]`.
- **Párrafos:** el primero sin sangría y los siguientes con sangría de 1 em, sin línea en blanco entre ellos `[BRI-ETS-062, BRI-ETS-063]`.
- **Citas de testimonio:** en cursiva y con un cuerpo mayor, sin comillas añadidas aparte de las suyas. Se distinguen de la voz del narrador con un solo recurso, la cursiva `[BRI-ETS-066]`.
- **Color:** texto casi negro (#1c1c1c) y pies en gris oscuro (#5c5c5c), sobre blanco. Ningún color de acento.

### Paratexto que añado (necesita tu aprobación)

- **Folio:** solo el número de página, en 8 pt, en el margen inferior y alineado con el borde derecho de la mancha. No va en la portada ni en las láminas a sangre.
- **Firma:** en la portada, bajo la entradilla.
- **No añado** cornisas, índice, colofón, créditos ni textos de presentación.

## 3. Solución: plan de páginas

Son 16 páginas. Los ID son los de `contenido_v01.md`.

| Pág. | Contenido | Tipo de página |
|---|---|---|
| 1 | F01 · E02 · E03 · E04 · firma | Portada. F01 a sangre en la mitad izquierda; titular, entradilla, pie y firma a la derecha |
| 2 | E05 · F02 · E07 · E08 | Columna de texto a la izquierda y foto principal a la derecha |
| 3 | E09 · F03 · E11 · E12 | Apertura de «Beli Bryag»: foto a la izquierda; rótulo y texto a la derecha |
| 4 | E13 · F04 · E15 · E16 | Texto a la izquierda; horizontal arriba a la derecha y la cita debajo de ella |
| 5 | E17 · E18 · F05 · E20 | Apertura de «Sus habitantes»: rótulo y texto a la izquierda; foto a la derecha |
| 6 | E21 · F06 · E23 · E24 | Foto a la izquierda; texto y cita a la derecha |
| 7 | E25 · F07 · E27 · E28 | Cita y texto a la izquierda; foto a la derecha |
| 8 | F08 · E30 · E31 | Retrato del nieto en grande, con la cita al lado |
| 9 | F09 · E33 · E34 | Horizontal a la izquierda; texto a la derecha |
| 10 | F10 · E36 | Lámina: retrato del abuelo, solo en la página |
| 11 | E37 · E38 · F11 · E40 | Texto a la izquierda; foto a la derecha |
| 12 | E41 · E42 · F12 · E44 | Apertura de «Transición energética»: foto a la izquierda; rótulo y texto a la derecha |
| 13 | E45 · F13 · E47 · E48 | Horizontal arriba; dos bloques de texto |
| 14 | E49 · F14 · E51 · E52 | Texto a ambos lados de la foto, en el orden de lectura |
| 15 | E53 · E54 · E55 · F15 · E57 · E58 | Apertura de «Conclusión»: texto y horizontal |
| 16 | F16 · E60 | Cierre: lámina vertical a sangre, con su pie |

Este plan es la variante de referencia `[GER-DP-035]`. Si al componer una página no funciona, cambio la página y lo anoto en la memoria, pero nunca cambio el orden.

## Próximo paso

Cuando apruebes este programa y las correcciones, compongo dos páginas representativas (la portada y una página de texto con foto) y te las enseño antes de hacer el resto (puerta 2).
