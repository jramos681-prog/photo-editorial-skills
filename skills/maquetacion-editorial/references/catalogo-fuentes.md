Explica cómo obtener y leer el catálogo de familias tipográficas que Typst ve en el proyecto, y qué pide cada clase de letra. Consúltalo después de decidir en `references/tipografia.md` qué clase de letra pide el documento, y lee solo el grupo que necesites.

# Catálogo de fuentes

## Cómo obtenerlo

El catálogo es un archivo generado en la carpeta del encargo, `maquetacion/catalogo.md`:

```
python scripts/catalogo_fuentes.py --config maquetacion/config.md
```

La carpeta propia se indica con `carpeta_fuentes` en `maquetacion/config.md`. El catálogo se vuelve a generar cuando cambian las fuentes de esa carpeta, las del sistema, los idiomas o las notas de licencia de la configuración. El script no vigila los cambios: hay que ejecutarlo otra vez. No se edita a mano.

Cada familia ocupa una línea. El catálogo reparte las familias en tres grupos. **Aptas para texto**: las fuentes con archivo propio que cubren el juego completo de caracteres de los idiomas configurados y cuyo permiso técnico (`OS/2.fsType`) deja incrustarlas en el PDF. **Solo para títulos y rótulos**: las que se pueden incrustar pero no cubren ese juego completo; el catálogo dice qué caracteres faltan, y se pueden proponer para un titular, un rótulo o una portada cuando el texto que se escribe con ellas no usa esos caracteres. **No aptas**: las que no se pueden incrustar o no se pueden leer; aparecen con un motivo breve y no se proponen. Las fuentes que trae Typst llevan la marca «incluida en Typst (OFL); cobertura no medida». En cada familia utilizable se indican el permiso de incrustación cuando se puede comprobar, la nota de licencia (la que declara el archivo y la que se haya escrito en la configuración) y, cuando hay archivo que medir, las versalitas, la clase de las cifras por defecto, las alternativas OpenType y las métricas disponibles (*x*, *M*, *av.* y *CPL*); si constan, también las marcas `preferida` y `evitar`.

## Cómo leer el catálogo

- **Qué se mide.** Cobertura de caracteres, permiso de incrustación, versalitas, clase de las cifras por defecto, alternativas OpenType y métricas de la cara representante (*x*, *M*, *av.* y *CPL*), con fontTools, en los archivos de la carpeta propia y, si están activadas, en las fuentes del sistema. Las versalitas se anuncian como `VC` cuando el archivo trae `smcp`, con `c2sc` cuando consta; `sin VC` significa que no hay `smcp`. Las cifras se anuncian por su clase cuando se puede determinar; si falta algún dígito, aparece «no medidas». `alt.` lista las alternativas de cifras presentes: `lnum`, `onum`, `tnum`, `pnum`. La licencia que declara el archivo y el permiso técnico de incrustación son datos distintos. El grupo de cada familia sale de la cobertura y del permiso de incrustación: para texto se exige el juego completo de cada idioma configurado, aunque el texto no use todos sus caracteres; para un titular, un rótulo o una portada basta con que la fuente cubra los caracteres que se escriben con ella, y `control_pdf.py` da fallo grave si en el PDF aparece un carácter que la fuente no tiene. El catálogo no lleva fecha de medición: antes de usar una familia, comprobar que sigue instalada y revisar su licencia.
- **Alcance.** Solo lo que Typst ve (`typst fonts`). Si una familia instalada no aparece, se comprueban la carpeta de fuentes de la configuración y el nombre con el que Typst la conoce.
- **Licencias.** Sin permiso de incrustación la familia no sirve para un PDF. Las de licencia comercial o del sistema se usan solo conforme a sus permisos de incrustación y a sus términos; no se redistribuyen ni se incluyen en paquetes compartidos. Que técnicamente pueda incrustarse no implica una licencia abierta.
- **Estilos.** *Estilos*: los que trae el archivo, o los ejes si es variable (rango y valor por defecto); se leen en el espécimen. *Falta*: estilos ausentes (sin cursiva o sin negrita, no usarla para texto con énfasis). *VC*: versalitas, y verdaderas cuando hacen falta.
- **Comparar familias.** El catálogo mide con fontTools la cara representante de cada familia. *x*, *M*: altura de x y de mayúscula en fracción de em; si se toman del dibujo y no de OS/2, la línea lo avisa con «alturas del contorno». *av.*: mm por carácter medio a 10 pt, calculado con los caracteres de una muestra neutra del idioma principal que están en la fuente. *CPL*: caracteres por línea en 140 mm a 10 pt (referencia para comparar familias, no medida recomendada). El avance no incluye kerning ni ligaduras, así que el CPL es una estimación.
- **Cifras.** El catálogo indica la clase de las cifras por defecto cuando puede determinarla a partir de los dibujos de 0 a 9; si falta algún dígito, muestra «no medidas»: *alin.* alineadas o *ant.* antiguas (de texto); *tab.* tabulares (mismo ancho) o *prop.* proporcionales. `alt.` lista las alternativas OpenType presentes (`lnum`, `onum`, `tnum`, `pnum`); en Typst se piden con `number-type` y `number-width`. Que falte una alternativa no quiere decir que falten esas cifras: pueden ser las de por defecto. Una familia sirve para cifras de texto si las trae por defecto o tiene `onum`, y para columnas de cifras si son tabulares por defecto o tiene `tnum`. Antes de confiar en una alternativa, se comprueba con un espécimen en Typst.
- **Al elegir, comprobar en Typst.** Una variable cuyo peso por defecto no es Regular pide el peso explícito. La altura de x y la de mayúscula medidas sobre el dibujo no siempre coinciden con las declaradas en OS/2. Los glifos ausentes del PDF compuesto los señala `python scripts/control_pdf.py documento.pdf` (`.notdef` y U+FFFD). El control marca como fallo cualquier fuente sin incrustar y da un aviso si una fuente no se puede verificar.
- **Carácter.** Las notas de cada grupo son genéricas de la clase y van marcadas *[nota]*; la elección concreta se razona con el documento (ver `references/tipografia.md`, decisión 5).

## 1. Grotescas

*[nota]* Palo seco de tradición grotesca y neogrotesca. Para lectura continua piden algo más de interlínea que una romana renacentista `[TSC-FOB-031, MB-GRID-025]`; en columnas estrechas suelen ir mejor en bandera `[BRI-ETS-035, BRI-ETS-037]`.

## 2. Romanas de texto

*[nota]* Romanas para lectura continua de distintas tradiciones; conviene situar cada una en su genealogía y comprobar su cursiva y sus cifras de texto antes de elegirla `[BRI-ETS-392–395, BRI-ETS-398]`. Las *revivals* digitales se prueban impresas en cuerpo de texto `[BRI-ETS-382, BRI-ETS-383]`.

Bringhurst desaconseja combinar Helvetica y Palatino entre sí (y con Baskerville o Times): parten de ideas incompatibles `[BRI-ETS-391]`.

## 3. Titulares con remate

*[nota]* Romanas pensadas para cuerpos grandes; casi todas sin familia completa, así que sirven para titulares y portadas, no para texto con énfasis `[MB-GRID-099]`.

## 4. Didónicas

*[nota]* Contraste fuerte y eje vertical. Bringhurst las ve poco aptas para lectura continua por el deslumbramiento de astas y perfiles `[BRI-ETS-607]`; Tschichold solo admite papel blanco puro con Bodoni, en cuerpos y páginas grandes y con algo de textura `[TSC-FOB-100]`.

## 5. Egipcias

*[nota]* Remates gruesos y poco contraste (tradición realista); trazo robusto que, como las romanas robustas, pide más interlínea `[TSC-FOB-031]`.

## 6. Geométricas

*[nota]* Palo seco construido sobre círculo y recta (tradición modernista geométrica); cuidado con la altura de x baja de varias de ellas al fijar cuerpo e interlínea `[BRI-ETS-053]`.

## 7. Estrechas y de cartel

*[nota]* Anchura condensada: para titulares o falta de espacio, no para texto corrido `[MB-GRID-016]`; Tschichold asocia los tipos condensados a formatos esbeltos `[TSC-FOB-039]`.

## 8. Monoespaciadas

*[nota]* Ancho fijo: propias de código y datos tabulares; fuera de ahí, ver el error típico 12 de `references/antipatrones.md`.

## 9. Fantasía y rotulación

*[nota]* Letras de carácter marcado o de uso específico (rotulación técnica, pixel, caligráfica, cartel). Bringhurst advierte contra las fuentes temáticas elegidas por el asunto literal `[BRI-ETS-387, BRI-ETS-388]`; si se usan, que sea por el concepto del documento y en pocas palabras.

## Fuentes

- Notas de grupo: Bringhurst (BRI-ETS-035, 037, 053, 382, 383, 387, 388, 391–395, 398, 607), Tschichold (TSC-FOB-031, 039, 100), Müller-Brockmann (MB-GRID-016, 025, 099).
