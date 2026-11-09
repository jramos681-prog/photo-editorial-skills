> Algunas partes de este archivo se han tomado de otros proyectos o se inspiran en ellos, y aquí están traducidas y adaptadas; el origen, las licencias y los avisos están en `NOTICE` (raíz).

Cubre la decisión 12 (comprobación final y antipatrones): léelo antes de dar por terminada cualquier entrega, y al revisar una maqueta propia o ajena.

# Comprobación final y antipatrones

**Capa revisable, fechada en noviembre de 2026.** Los tics de los modelos y el estado de las herramientas cambian; esta lista se revisa cuando cambien. Las afirmaciones sobre capacidades de motores o versiones llevan `[revisar antes del uso]`.

**Límite de transferencia.** Se traslada el **tic visual** tal como se ve en la página impresa, no unidades, CSS, *breakpoints* ni reglas de interfaz. Una cifra solo vale si procede de un libro.

## 1. Principios de la comprobación

- **Verificado no es visto.** «Construcción verificada, visuales sin confirmar»: que compile o pase el script no basta para decir «listo»; si las páginas no se han renderizado a PNG e inspeccionado, la entrega es provisional. — *Regla de la skill.*
- **Se comprueba el PDF, no el código.** Desbordes, ríos, viudas, recortes, glifos vacíos y resolución efectiva solo existen en el objeto exportado `[control_pdf.py]`. — *Limitación técnica.*
- **Comprobar contra la retícula en cada fase**: interlineado constante, columnas alineadas, sin deformaciones `[BRI-ETS-665]`. — *Heurística.*
- **Lo incidental también cuenta**: folios, notas, créditos y datos editoriales reciben atención plena `[BRI-ETS-023]`. La tipografía debe invitar al texto, revelar su tono y sentido, aclarar la estructura, vincular elementos e inducir un reposo enérgico `[BRI-ETS-024]`; sirve de pregunta final de revisión. — *Heurística.*
- **Restar antes que añadir.** «La página está terminada cuando no queda nada que quitar» `[Saint-Exupéry]`: cada filete, marco, fondo o adorno debe tener una función; si al ocultarlo se mantienen sentido y jerarquía, sobra. Pulido final sin añadir elementos (ver `references/programa.md`). — *Heurística.*
- **Ninguna receta da profesionalidad.** Ni el crema ni la letra con remates confieren rigor por sí mismos; el diseño se deduce de la obra y del encargo `[introducción de SKILL.md]`. Esta lista sirve para detectar clichés, no para sustituir un estilo de casa por otro: solo son prohibiciones las reglas de la skill. — *Regla de la skill.*
- **La aprobación es del autor** y no se presume por silencio `[regla 6 de SKILL.md]`. — *Regla de la skill.*

## 2. Modos del documento (analogía)

Los modos del documento se distinguen así:

- **Lectura y operación** (dosier, candidatura, memoria técnica, hoja de sala, catálogo razonado): prima la estabilidad, la previsibilidad y la legibilidad.
- **Persuasión y experiencia** (cubierta de fotolibro, cartel, invitación singular): admite un punto de vista rotundo, contrastes de escala y asimetrías, siempre derivados del concepto de la serie y no de ornamento genérico.

Medida, márgenes y color se deciden en `references/tipografia.md` y `references/reticula.md` según el encargo; el modo orienta, no fija valores.

## 3. Catálogo de tics: señales de revisión

Cada tic es un **patrón frecuente que se contrasta con el propósito**. Si el encargo lo justifica (y se puede decir por qué), se mantiene.

1. **Crema + romana de alto contraste + terracota.** Fondo pergamino, titulares de alto contraste y acento arcilla, asignados sin motivo: confunden calidez con rigor. Que en el fotolibro de autor y la publicación de arquitectura el soporte suela ser blanco, el negro estructural y el color fotográfico es una valoración, en parte inferida `[inferencia]`, no una ley. El tic incluye cualquier fondo tintado (crema, beis, gris cálido o frío) elegido sin motivo; un gris neutro no lo es. Un fondo que el programa llame neutro tiene que tener los tres canales iguales; si lleva matiz, el programa dice qué de las fotos o del soporte lo pide. *Lo justificaría:* un papel o una letra elegidos por la obra (ver `references/fotolibro-objeto.md`, tono del papel).
2. **Degradados púrpura** en cabeceras o fondos: cliché de software generado.
3. **Azul como acento por defecto**, sin examinar.
4. **Azul marino y dorado** para simular prestigio.
5. **Fondos negros masivos** como efecto. Las fuentes lo dan por agresivo y mal impreso; los riesgos de secado, repintado o cobertura de tinta dependen de cobertura, proceso, papel y perfil, y se verifican con el impresor. Müller-Brockmann usa fondos oscuros para dar contraste y luminosidad a la foto, con control del soporte y del secado `[MB-GRID-792]`. *Lo justificaría:* una serie que lo pida, probado en el papel.
6. **Título centrado con filete fino debajo** como solución automática. *Distinto de* una portada centrada razonada (ver `references/tipografia.md`).
7. **Sombras duras desplazadas**: fuera de un lenguaje neobrutalista elegido para el documento, la sombra sin desenfoque parece un efecto añadido y no crea profundidad; no se impone como recurso por defecto.
8. **Tarjetas genéricas**: cajas del mismo tamaño con icono, titular y texto usadas como estructura de la página. Son el contenedor fácil, y metidas unas dentro de otras siempre están mal. Para la maquetación básica no hacen falta: bastan el blanco y la alineación.
9. **Rótulo superior por costumbre** (versales pequeñas muy espaciadas sobre cada titular): si repite lo que dice el titular o nombra lo que ya se ve («Biografía», «Obra», «Contacto»), sobra. Solo se justifica si aporta un dato que el titular no tiene y que el lector necesita (la sala, la serie, la sección de un catálogo extenso), con el mismo tratamiento en todo el documento. En un dosier o un porfolio de una sola voz casi nunca hace falta.
10. **Puntos medios encadenados** (`Proyecto · 2026 · Lugar`) en lugar de articulación sintáctica o espacial.
11. **Numeración 01 / 02 / 03** en apartados cuyo orden no aporta información al lector.
12. **Monoespaciada para aparentar técnica** en pies o fechas; vale para código, datos tabulares o medidas, y fuera de ahí hay que decir por qué.
13. **Glifos Unicode y emojis** usados de adorno, fuera del sistema de la fuente.
14. **Recortar la foto para llenar el marco** (`object-fit: cover`): mutila la composición. **Prohibido** `[regla 2 de SKILL.md]` (*regla de la skill*).
15. **Márgenes iguales en los cuatro lados.** En el libro encuadernado y el canon de novenos, las fuentes piden pie mayor, exterior mayor que interior y lomo que cuente con la curvatura; los libros lo formulan como tradición, no como ley universal (ver `references/reticula.md`). En una lámina suelta o un panel la relación se razona aparte.
16. **Líneas de más de 85 caracteres**: una sola columna a todo lo ancho de un A4 en cuerpo 10.
17. **Ortotipografía descuidada**: comillas rectas, guiones donde el autor escribió una raya, sin espacio duro ante % o en millares `[control_pdf.py]`. Detalle en `references/tipografia.md`.
18. **Cubierta desligada del interior**, con formas libres y colores ajenos a la retícula `[MB-GRID-814]`.
19. **Rayas introducidas por la skill** en textos que el autor no escribió.

## 4. Vocabulario y pruebas de crítica

- **Entrecerrar los ojos**: con la doble página en miniatura o desenfocada, ¿se identifican el elemento principal, el secundario y los grupos más importantes, en ese orden?
- **Borrado**: ocultar un filete, marco o fondo; si se entiende igual o mejor, sobraba.
- **Rótulo superior**: taparlo; si el título basta, fuera.
- **Permuta del punto medio**: si `A · B` no admite `B · A`, los términos no son simétricos y piden sintaxis.
- **Proximidad**: el blanco entre titular y su texto, claramente menor que el que lo separa del bloque anterior (las fuentes proponen al menos la mitad); agrupar por cercanía antes que con líneas. *Heurística ajustable.*
- **Contención cromática**: las fuentes proponen como mucho un acento funcional (o ninguno), que no pase de un 5 % de la superficie y se use al menos dos veces como sistema; texto en negro. *Referencia para revisar, no paleta obligatoria.*
- **Informe de incidencias** en cinco columnas: `Gravedad | Dónde | Antes | Después | Por qué`, y no se da por bueno mientras quede una incidencia alta (caja, glifos, anonimato, resolución). El «aprobado» final es del autor.

## 5. Severidad

Valores por defecto, configurables según encargo e impresor:

- **Fallo (bloquea la entrega; ninguna excepción lo levanta)**: páginas fuera de las pedidas o por encima de lo que admiten las bases; tamaño de corte fuera de la tolerancia; `.notdef` o U+FFFD; un carácter usado en el PDF que su fuente no tiene; fuentes sin incrustar; peso por encima del límite de las bases, en MB decimales (1 MB = 1 000 000 bytes; el informe da además los bytes); si se activa `--exigir-metadatos`, falta el título o el creador; un dato personal en una entrega anónima; texto fuera del corte o en la franja de seguridad de 3,0 mm por defecto; dibujo fuera del corte más el sangrado, o en la franja de seguridad por un borde que no alcanza; imagen fuera del corte más el sangrado; el texto no queda exento por declararse a sangre y un dibujo solo cuenta como sangre en los bordes del corte que cruza o toca, siempre dentro del sangrado; imagen por debajo de las ppp mínimas configuradas (200 por defecto; el fallo real depende de la especificación del impresor), salvo con `--copias-trabajo`, que informa sin juzgar; cualquier violación de reglas de la skill (recorte automático [regla 2 de SKILL.md], recorte o alteración de imágenes de una secuencia aprobada [regla 1 de SKILL.md], deformación de la proporción nativa, o texto sobre fotografías salvo petición expresa [regla 2 de SKILL.md]).
- **Fallo heurístico (bloquea, salvo excepción declarada)**: la medida de un bloque de prosa. Solo se juzga la prosa de tres líneas útiles o más, bloque por bloque, y su mediana sale de los límites duros de 40 a 85 cpl por defecto.
- **Aviso (revisión)**: imagen entre el mínimo y el objetivo de ppp (200–300 por defecto), que se decide con el autor según soporte y distancia; medida con la mediana fuera de 45–75 cpl, pero dentro de 40–85; también se avisa si, con la mediana dentro de los límites duros, más del 2 % de las líneas útiles queda fuera de ellos; mancha por encima del 60 % en páginas que no son láminas a sangre (revisión manual); si no falta ningún carácter usado, aviso cuando un archivo medible no cubre algún carácter del juego que el PDF no usa (sirve para títulos y rótulos, no para texto corrido); fuentes que no se pueden verificar; el mismo tipo de doble página en más de dos pliegos seguidos (umbral experimental; revisión manual); cualquier adjunto en una entrega anónima; una excepción declarada que no llega a aplicarse.

## 6. Qué comprueba `scripts/control_pdf.py`

Solo lo que el código hace (cada control da `ok`, `aviso`, `fallo`, `fallo heurístico`, `excepción declarada` o `no-aplica`; el script termina con 0 si no hay fallos, con 1 si hay un fallo duro o heurístico o si el PDF no se puede abrir, y con 2 si la llamada o la configuración no son válidas):

1. **Páginas**: número exacto o rango (`--paginas`, `--paginas-min`, `--paginas-max`).
2. **Tamaño de corte** de cada página frente a `--tamano`, con tolerancia por defecto de 0,5 mm (`--tolerancia`).
3. **Fuentes**: inventario, incrustación y glifos. Una fuente sin incrustar o un glifo `.notdef` o U+FFFD es fallo; una fuente que no se puede verificar, aviso. **Cobertura** del juego de caracteres de los idiomas configurados: se mide con los archivos de `carpeta_fuentes` (`maquetacion/config.md`; `sistema: sí` incluye las instaladas) y, si no se encuentra un archivo medible, con el programa que el PDF lleva incrustado. Un carácter usado que la fuente no tiene es fallo. Si no falta ningún carácter usado, una fuente con archivo medible a la que le falten caracteres del juego que el PDF no usa genera aviso («sirve para títulos y rótulos, no para texto corrido»); un subconjunto incrustado que cubre los caracteres usados puede quedar en «ok», con la nota de que el juego completo no se puede comprobar. Si no falta ningún carácter usado y queda una fuente sin verificar, el control avisa; si no hay archivos de fuentes disponibles ni fuentes verificadas, la cobertura queda en «no-aplica».
4. **Imágenes**: ppp efectivos calculados a partir de la matriz de transformación de cada imagen; aviso bajo `--ppi-objetivo` (300) y fallo bajo `--ppi-minimo` (200) o cuando la matriz no se puede medir; con `--copias-trabajo` no se juzga y se informa del lado corto que necesitará cada archivo final.
5. **Tamaño del archivo** frente a `--max-mb`, en MB decimales (1 MB = 1 000 000 bytes; el informe da además los bytes).
6. **Metadatos**: informa `title`, `author`, `creator` y `producer`; si faltan el título o el creador, avisa, y con `--exigir-metadatos` lo trata como fallo.
7. **Anonimato** (`--anonimo`, con `--nombres`): texto normalizado; correos, URL y teléfonos (distinguidos de fechas y cifras); nombres del autor; en texto visible, propiedades, XMP, anotaciones, enlaces, formularios y adjuntos (varias decodificaciones, PDF adjuntos hasta tres niveles). Cualquier adjunto da al menos aviso; un dato personal, fallo.
8. **Medida**: cpl reales por bloque (mediana, p10, p90); aviso si la mediana queda fuera de 45–75 cpl, pero dentro de 40–85, y también si más del 2 % de las líneas útiles queda fuera de los límites duros; fallo heurístico si la mediana queda fuera de 40–85 (`--cpl-min`, `--cpl-max`, `--cpl-duro-min`, `--cpl-duro-max`). Solo se juzga la prosa de tres líneas útiles o más. `--excepciones` acepta un YAML o JSON con una lista de `{pagina, control, bloque, tipo, motivo}`, solo para el control `medida`: `bloque` es el texto inicial o el índice (desde 1), `tipo` es cita, pie, titular u otro, y `motivo` no puede quedar vacío. El bloque afectado pasa a «excepción declarada» y el resto se sigue midiendo igual; una excepción que no se aplica se informa.
9. **Fuera de caja** (`--margen-seguro`, 3 mm por defecto): el texto queda dentro del corte y del área segura, sin exención por declararse a sangre. Un dibujo solo cuenta como sangre en los bordes del corte que alcanza, al cruzarlos o tocarlos, sin tolerancia; en los demás bordes respeta el área segura y el dibujo entero queda dentro del sangrado. Las imágenes deben quedar dentro del corte más el sangrado. La tolerancia de `--tolerancia` se aplica al límite del sangrado de dibujos e imágenes y a la franja de seguridad de los dibujos, no al texto ni a los bordes alcanzados.

**No lo comprueba el script** (revisión manual u otras herramientas):

- Nombre externo del archivo (y su versión `_v01`, sin acentos ni espacios: *regla de la skill*), nombres exigidos por las bases y metadatos de las imágenes sueltas.
- Perfiles RGB/CMYK, ICC, *output intent*, cobertura de tinta, PDF/X, marcas de corte y conformidad de cajas con la especificación del impresor.
- Que cada foto conserve su proporción nativa y no sufra recortes automáticos ni alteración de una secuencia aprobada (el control de caja no lo demuestra): se compara con los archivos del autor.
- Texto dentro de imágenes o planos escaneados (haría falta OCR) y adjuntos cifrados.
- Render y revisión visual: `scripts/hoja_contactos.py` renderiza a PNG y monta hojas de contactos por pliegos o por páginas; la mirada es del agente y del autor.
- Coherencia de la serie, ritmo de los pliegos, pertinencia del blanco y del tono: juicio del autor tras ver las páginas.

## 7. Reglas de la skill en la comprobación

- Español como idioma base; otras lenguas en versiones separadas.
- Nada inventado: lo no confirmado, `[Por verificar]`.
- Proporción nativa sin deformar; sin recortes automáticos (regla 2 de `SKILL.md`) ni alteración o recorte de una secuencia aprobada (regla 1 de `SKILL.md`); sin texto sobre fotografías salvo petición expresa (regla 2 de `SKILL.md`).
- Render a PNG y revisión antes de cada entrega; aprobación explícita del autor.
- Nombres de archivo según `maquetacion/config.md` (por defecto, con versión `_v01` y sin acentos ni espacios); las bases mandan por encima.

## Dónde discrepan

- **Typst frente a motores CSS de impresión** `[revisar antes del uso]`. PrinceXML, WeasyPrint o Vivliostyle generan PDF/X, marcas de corte y CMYK. Typst 0.15.1 maneja sangrado y escribe `TrimBox`; admite CMYK en elementos y en imágenes CMYK como DeviceCMYK, sin perfil ICC ni `output intent`. Las imágenes RGB probadas se exportan con el perfil sRGB de Typst, sin conservar el perfil ICC de origen. Typst no exporta PDF/X ni dibuja marcas de corte; las pruebas con CMYK y PDF/A-2b y PDF/A-4 fallaron por falta de perfil CMYK. Para convocatorias y visionados basta el PDF de Typst con sangrado; si un impresor exige PDF/X o CMYK calibrado, se avisa al autor para completar la salida con otra herramienta.
- **Línea base estricta frente a láminas.** Bringhurst subordina los elementos a la línea base; en un libro de fotografía, forzar la altura de una imagen a un múltiplo de línea obligaría a deformarla o recortarla. Criterio: prosa, tablas de obra, pies y folios en la línea base; las láminas conservan su proporción y rompen la rejilla de forma declarada.

## Errores típicos

- Dar por buena una entrega porque compila, sin ver los PNG `[regla 6 de SKILL.md]`.
- Suponer que una fuente sirve porque está instalada, sin comprobar « » o — `[control_pdf.py; catálogo]`.
- Recorte automático o deformación de una foto para que encaje `[regla 2 de SKILL.md]`, o recorte de imágenes de una secuencia aprobada `[regla 1 de SKILL.md]`.
- Dejar nombres o metadatos personales en una convocatoria ciega `[control_pdf.py]`.
- Líneas de más de 85 caracteres o columnas de menos de 40 con ríos `[control_pdf.py]`.
- Llenar el blanco con filetes, tarjetas, iconos o números artificiales.
- Diseñar páginas sueltas en lugar de dobles páginas.
- Atribuir al script controles que no hace (color, PDF/X, nombre de archivo, proporción respecto al original).

## Comprobar al final

1. `python scripts/control_pdf.py` con los parámetros del encargo (`--tamano`, `--paginas`, `--max-mb`; `--anonimo --nombres` si procede; `--excepciones` si el encargo declara bloques de medida): sin fallos; avisos explicados.
2. Controles manuales de la lista «No lo comprueba el script».
3. Render a PNG y hoja de contactos (pliegos o páginas, según el programa); revisión con las pruebas de la sección 4 y los cinco servicios de `[BRI-ETS-024]`.
4. Catálogo de tics recorrido: cada tic presente, justificado o eliminado.
5. Ortotipografía (`references/tipografia.md`) y requisitos de las bases (`references/generos.md`).
6. Presentación al autor con el informe de incidencias; esperar su aprobación explícita.

## Fuentes

- Bringhurst, *The Elements of Typographic Style* v3.0: BRI-ETS-023, 024, 665. Müller-Brockmann, *Grid Systems in Graphic Design*: MB-GRID-792, 814.
- `scripts/control_pdf.py` y `scripts/hoja_contactos.py`.
