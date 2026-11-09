// editorial.typ — biblioteca paramétrica de maquetación editorial
//
// Versión mínima de Typst comprobada: 0.15.1.
//
// Esta biblioteca no impone estilo: ni familias, ni cuerpos, ni colores. Calcula
// geometría de página, retícula y línea base; coloca fotografías con su proporción
// nativa y compone tablas a partir de datos. Los valores de respaldo son neutros
// para que el documento decida todo lo visible.
//
// Índice de la API pública (el detalle está en el comentario de cada `#let`):
//
//   Página
//     margenes_canon(ancho, alto, canon)   márgenes de un canon cerrado
//     area_texto(ancho, alto, canon)       área de texto de ese canon
//     pagina(...)                          página con corte, márgenes y sangrado
//     pliego(...)                          doble página con lomo
//   Rejilla y línea base
//     rejilla_base(base, modo, ...)        interlineado ajustado a la base
//     redondear_base(alto, base)           sube una altura al múltiplo de base
//     lineas_en(alto, base)                módulos de base que caben en un alto
//     reticula(...)                        retícula modular de columnas y filas
//   Campos
//     geom(reticula, col, row, ...)        (x, y, ancho, alto) de un campo
//     campo(reticula, col, row, ...)       bloque del tamaño exacto del campo
//     colocar(reticula, col, row, ...)     coloca contenido en un campo
//     caracteres_por_linea(...)            cpl estimados de una caja
//     capa_depuracion(...)                 retícula y líneas base para QA
//   Imagen y pie
//     foto(ruta, reticula, ...)            imagen a proporción nativa en un campo
//     pie(texto, ...)                      pie de foto ajustado a la base
//   Tablas
//     tabla_datos(datos, campos, ...)      tabla genérica a partir de datos
//     tabla_obras(obras, ...)              lista de obra
//     tabla_cronologia(eventos, ...)       cronología
//
// Para usarla desde otro proyecto, copia este archivo dentro del proyecto, por
// ejemplo, en `typst/editorial.typ`, e importa lo que necesites:
//
//   #import "typst/editorial.typ": pagina, reticula, foto
//
// Rutas de imagen: `foto` recibe la ruta y la resuelve como cualquier ruta
// escrita dentro de esta biblioteca, es decir, respecto al archivo de la
// biblioteca y no al documento que la importa. Una ruta que empieza por `/` se
// resuelve contra la raíz de Typst (`--root`), y por eso es la forma que no
// depende de dónde esté copiada la biblioteca:
//
//   #foto("/images/foto.png", r)
//
// Una ruta relativa se busca junto a la biblioteca: con esta en `typst/`,
// `#foto("images/2a1.png", r)` falla con
// «file not found (searched at …\typst\images\2a1.png)».
//
// Ejemplo mínimo (con la biblioteca copiada y una imagen en `images/foto.png`):
//   #import "typst/editorial.typ": reticula, foto
//   #set page(width: 100mm, height: 100mm, margin: 0pt)
//   #let r = reticula(ancho: 100mm, alto: 100mm,
//     columnas: 1, filas: 1, canal_h: 0mm, canal_v: 0mm)
//   #foto("/images/foto.png", r)
//
// Compila desde esa raíz con `typst compile --root . main.typ`.
//
// Aritmética medida en Typst 0.15.1:
//   Con `text(top-edge: t, bottom-edge: b)` y `par(leading: l)`, siendo
//   Δ = t − b, la distancia entre líneas base consecutivas es
//
//       S = l + Δ
//
//   y la altura de un párrafo de N líneas es
//
//       H(N) = N · S − l
//
//   (comprobado con l = 10pt, t = 10pt, b = 0pt → H = 10, 30, 50, 70 pt y
//   S = 20 pt; con l = 13pt, t = 0pt, b = 0pt → H = 0, 13, 26, 39 pt y S = 13 pt.)
//
//   De ahí salen los dos modos de `rejilla_base`:
//
//   - "caja":     t = base, b = 0, l = 0  → S = base y H(N) = N · base.
//                 Las líneas base caen en base, 2·base, … N·base.
//   - "baseline": t = 0, b = 0, l = base  → S = base y H(N) = (N−1) · base.
//                 Las líneas base caen en 0, base, … (N−1)·base.
//
//   En ambos, todo bloque de N líneas mide un múltiplo entero de la base.
//
// Cánones de página (márgenes en mm, W = ancho, H = alto):
//
//   - "novenos" (Tschichold / van de Graaf, proporción 1:2 / 1:2):
//       interior = W/9, exterior = 2W/9, superior = H/9, inferior = 2H/9
//       área de texto = 2W/3 × 2H/3 = 44,4 % de la página.
//       Sobre una página 2:3 las proporciones de margen son exactamente
//       2:3:4:6 (interior:superior:exterior:inferior).
//
//   - "van-de-graaf" (construcción por diagonales):
//       el área de texto tiene la altura del ancho de página (H_ta = W) y es
//       semejante a la página. Resolviendo con exterior = 2·interior e
//       inferior = 2·superior:
//         superior = (H−W)/3,  inferior = 2(H−W)/3
//         área_ancho = W²/H,   interior = W(1−W/H)/3, exterior = 2W(1−W/H)/3
//       En A4 da 20,5 / 41,0 / 29,0 / 58,0 y un área de 148,5 × 210 mm, que es
//       exactamente el A5 (regla ISO-half, 50 % de la página). Sobre 2:3 coincide
//       con "novenos" (44,4 %). La proporción del área no es constante: es
//       (W/H)² de la página (en 240 × 300, 64 %), porque la construcción fija la
//       altura del área al ancho de página. Exige H ≥ W; en apaisado se detiene
//       con un error explícito.

// ---------------------------------------------------------------------------
// 1. Página
// ---------------------------------------------------------------------------

/// Márgenes de un canon cerrado. Devuelve (interior, exterior, superior, inferior).
#let margenes_canon(ancho: 210mm, alto: 297mm, canon: "novenos") = {
  if canon == "novenos" {
    (
      interior: ancho / 9,
      exterior: 2 * ancho / 9,
      superior: alto / 9,
      inferior: 2 * alto / 9,
    )
  } else if canon == "van-de-graaf" {
    assert(
      alto >= ancho,
      message: "margenes_canon: van-de-graaf exige alto ≥ ancho (la altura del área de texto es el ancho de página)",
    )
    let u = (alto - ancho) / 3
    let v = ancho * (1 - ancho / alto) / 3
    (interior: v, exterior: 2 * v, superior: u, inferior: 2 * u)
  } else {
    panic("margenes_canon: canon desconocido «" + str(canon) + "»; use \"novenos\" o \"van-de-graaf\"")
  }
}

/// Área de texto resultante de un canon: (ancho, alto).
#let area_texto(ancho: 210mm, alto: 297mm, canon: "novenos") = {
  let m = margenes_canon(ancho: ancho, alto: alto, canon: canon)
  (ancho: ancho - m.interior - m.exterior, alto: alto - m.superior - m.inferior)
}

/// Normaliza un diccionario de márgenes admitiendo nombres en español o de Typst.
#let _normalizar_margenes(m) = {
  (
    interior: m.at("interior", default: m.at("left", default: 0pt)),
    exterior: m.at("exterior", default: m.at("right", default: 0pt)),
    superior: m.at("superior", default: m.at("top", default: 0pt)),
    inferior: m.at("inferior", default: m.at("bottom", default: 0pt)),
  )
}

/// Página con tamaño de corte, márgenes (explícitos o de canon), sangrado
/// opcional y paginación impar/par mediante interior/exterior.
///
/// - `margenes: auto` → se derivan del `canon`.
/// - `encuadernado: true` → margen `(inside, outside, top, bottom)`; el interior
///   cae a la izquierda en páginas impares y a la derecha en pares.
/// - `sangrado` se pasa a `page(bleed:)`; Typst define entonces el TrimBox.
/// - `depuracion` es contenido (normalmente `capa_depuracion(...)`) que se
///   coloca sobre el cuerpo, en el origen del área de texto. Solo para QA.
#let pagina(
  ancho: 210mm,
  alto: 297mm,
  margenes: auto,
  canon: "novenos",
  sangrado: 0mm,
  encuadernado: true,
  cabecera: none,
  pie: none,
  numeracion: none,
  fondo: none,
  depuracion: none,
  cuerpo,
) = {
  let m = if margenes == auto {
    margenes_canon(ancho: ancho, alto: alto, canon: canon)
  } else {
    _normalizar_margenes(margenes)
  }
  // En encuadernación el margen se declara por inside/outside; sin ella, el
  // interior hace de izquierda (documento de una cara).
  let margen = if encuadernado {
    (inside: m.interior, outside: m.exterior, top: m.superior, bottom: m.inferior)
  } else {
    (left: m.interior, right: m.exterior, top: m.superior, bottom: m.inferior)
  }
  page(
    width: ancho,
    height: alto,
    margin: margen,
    bleed: sangrado,
    binding: auto,
    header: cabecera,
    footer: pie,
    numbering: numeracion,
    background: fondo,
  )[
    #cuerpo
    // La capa de QA se dibuja al final para que quede por encima de las
    // imágenes, que es donde hay que comprobar la alineación.
    #if depuracion != none {
      place(top + left, dx: 0pt, dy: 0pt, depuracion)
    }
  ]
}

/// Lienzo de pliego para diseñar y revisar una doble página como unidad.
///
/// Produce **una sola página de Typst** del doble de ancho (2·ancho + lomo) con
/// dos paneles de `ancho × alto`, sus márgenes interiores hacia el lomo y una
/// marca opcional del lomo. No es una página del documento final: sirve para
/// componer y mirar la relación entre las dos páginas.
///
/// Convención: el pliego es [verso | recto], como en un libro. El panel
/// izquierdo (verso) lleva el margen interior a su derecha; el derecho (recto),
/// a su izquierda. El área de texto de cada panel mide lo mismo que en una
/// página suelta, así que las retículas y `foto`/`colocar` se usan igual:
///
///   #let m = margenes_canon(ancho: 340mm, alto: 220mm)
///   #let r = reticula(..area_texto(ancho: 340mm, alto: 220mm), columnas: 6, ...)
///   #pliego(ancho: 340mm, alto: 220mm, canon: "novenos",
///     izq: [ #colocar(r, 1, 1, colspan: 3)[…] #foto(ruta, r, col: 4, row: 1) ],
///     der: [ #colocar(r, 1, 1, colspan: 6)[…] ],
///   )
///
/// Del pliego al PDF final: un pliego no existe como página. Se maqueta página
/// a página con `pagina()` (mismo formato, mismos márgenes) y la pareja se
/// revisa con `scripts/hoja_contactos.py --modo pliegos`, que empareja las
/// páginas ya producidas. Una imagen que cruce el lomo se compone en una sola
/// página que se sangra por el lado interior, no con este lienzo.
#let pliego(
  ancho: 340mm,
  alto: 220mm,
  margenes: auto,
  canon: "novenos",
  lomo: 0mm,
  sangrado: 0mm,
  marca_lomo: true,
  tinta_lomo: rgb("#9aa0a6"),
  depuracion: none,
  izq: none,
  der: none,
) = {
  assert(lomo >= 0mm, message: "pliego: el lomo no puede ser negativo")
  let m = if margenes == auto {
    margenes_canon(ancho: ancho, alto: alto, canon: canon)
  } else {
    _normalizar_margenes(margenes)
  }
  let ancho_lienzo = 2 * ancho + lomo
  let margen_izq = (left: m.exterior, right: m.interior, top: m.superior, bottom: m.inferior)
  let margen_der = (left: m.interior, right: m.exterior, top: m.superior, bottom: m.inferior)
  page(width: ancho_lienzo, height: alto, margin: 0pt, bleed: sangrado)[
    #place(top + left, dx: 0pt, dy: 0pt, block(width: ancho, height: alto, inset: margen_izq)[
      #if depuracion != none { place(top + left, dx: 0pt, dy: 0pt, depuracion) }
      #izq
    ])
    #place(top + left, dx: ancho + lomo, dy: 0pt, block(width: ancho, height: alto, inset: margen_der)[
      #if depuracion != none { place(top + left, dx: 0pt, dy: 0pt, depuracion) }
      #der
    ])
    #if marca_lomo {
      place(
        top + left,
        dx: ancho + lomo / 2,
        dy: 0pt,
        line(length: alto, stroke: 0.3pt + tinta_lomo),
      )
    }
  ]
}

// ---------------------------------------------------------------------------
// 2. Línea base
// ---------------------------------------------------------------------------

/// Rejilla de línea base para un módulo `base`.
///
/// Devuelve un diccionario con:
///   - `base`: el módulo.
///   - `texto`: argumentos para `text(...)` (top-edge / bottom-edge).
///   - `par`: argumentos para `par(...)` (leading / spacing).
///   - `modo`: "caja" o "baseline".
///   - `redondear(alto)`: sube una altura al múltiplo entero de `base`.
///   - `lineas(alto)`: número de líneas base que caben (redondeo hacia abajo).
///   - `primera_base`: altura de la primera línea base respecto al borde superior.
///
/// `spacing` es la separación entre párrafos; se redondea a `lineas_parrafo`
/// módulos para que no rompa la rejilla (Bringhurst: el espacio de un bloque
/// debe ser múltiplo del interlineado).
#let rejilla_base(base: 13pt, modo: "caja", lineas_parrafo: 1) = {
  assert(base > 0pt, message: "rejilla_base: base debe ser positiva")
  assert(
    modo == "caja" or modo == "baseline",
    message: "rejilla_base: modo debe ser \"caja\" o \"baseline\"",
  )
  let texto = if modo == "caja" {
    (top-edge: base, bottom-edge: 0pt)
  } else {
    (top-edge: 0pt, bottom-edge: 0pt)
  }
  let par = (
    leading: if modo == "caja" { 0pt } else { base },
    spacing: lineas_parrafo * base,
  )
  (
    base: base,
    modo: modo,
    texto: texto,
    par: par,
    primera_base: if modo == "caja" { base } else { 0pt },
    redondear: alto => calc.ceil(alto / base) * base,
    lineas: alto => calc.floor(alto / base),
  )
}

/// Sube `alto` al múltiplo entero inmediato de `base`.
#let redondear_base(alto, base) = calc.ceil(alto / base) * base

/// Número entero de módulos de `base` que caben en `alto`.
#let lineas_en(alto, base) = calc.floor(alto / base)

// ---------------------------------------------------------------------------
// 3. Retícula modular
// ---------------------------------------------------------------------------

/// Retícula de columnas × filas con canales horizontales y verticales.
///
/// `ancho`/`alto` son los del área de texto (use `area_texto(...)` esparcido con
/// `..` para derivarlos del canon). `canal_v: auto` exige `interlineado` y toma
/// `lineas_canal × interlineado`, de modo que el canal vertical sea un múltiplo
/// entero del interlineado, para que los canales no desplacen de forma irregular
/// las líneas base del texto.
///
/// Campos calculados:
///   campo_w = (ancho − (columnas−1)·canal_h) / columnas
///   campo_h = (alto  − (filas−1)·canal_v)   / filas
///
/// Devuelve un diccionario con los parámetros de entrada y las dimensiones
/// calculadas (`canal_v`, `campo_w` y `campo_h` incluidos). Sus accesores internos
/// son `_geom`, `_campo` y `_colocar`; para usarlos desde el documento están las
/// funciones públicas `geom(...)`, `campo(...)` y `colocar(...)`. El cálculo de
/// caracteres por línea es una función separada: `caracteres_por_linea(...)`.
#let reticula(
  ancho: 140mm,
  alto: 198mm,
  columnas: 6,
  filas: 8,
  canal_h: 4mm,
  canal_v: auto,
  interlineado: none,
  lineas_canal: 1,
) = {
  assert(columnas >= 1 and filas >= 1, message: "reticula: columnas y filas deben ser ≥ 1")
  assert(canal_h >= 0pt, message: "reticula: canal_h no puede ser negativo")
  let cv = if canal_v == auto {
    assert(interlineado != none, message: "reticula: canal_v es auto y falta interlineado")
    assert(interlineado > 0pt, message: "reticula: con canal_v automático el interlineado debe ser positivo")
    assert(
      type(lineas_canal) == int and lineas_canal >= 1,
      message: "reticula: lineas_canal debe ser un entero ≥ 1 (" + str(lineas_canal) + ")",
    )
    lineas_canal * interlineado
  } else {
    assert(canal_v >= 0pt, message: "reticula: canal_v no puede ser negativo")
    canal_v
  }
  let cw = (ancho - (columnas - 1) * canal_h) / columnas
  let ch = (alto - (filas - 1) * cv) / filas
  assert(cw > 0pt, message: "reticula: las columnas y los canales no caben en el ancho")
  assert(ch > 0pt, message: "reticula: las filas y los canales no caben en el alto")

  let geom(col, row, colspan: 1, rowspan: 1) = {
    assert(col >= 1 and col <= columnas, message: "reticula.geom: col fuera de rango")
    assert(row >= 1 and row <= filas, message: "reticula.geom: row fuera de rango")
    assert(colspan >= 1 and col + colspan - 1 <= columnas, message: "reticula.geom: colspan se sale de la retícula")
    assert(rowspan >= 1 and row + rowspan - 1 <= filas, message: "reticula.geom: rowspan se sale de la retícula")
    (
      x: (col - 1) * (cw + canal_h),
      y: (row - 1) * (ch + cv),
      ancho: colspan * cw + (colspan - 1) * canal_h,
      alto: rowspan * ch + (rowspan - 1) * cv,
    )
  }

  // `clip: true` corta lo que no cabe en el campo: útil para detectar
  // desbordamientos en QA en vez de verlos como solapes silenciosos.
  let campo(col, row, colspan: 1, rowspan: 1, alinear: top + left, clip: false, cuerpo) = {
    let g = geom(col, row, colspan: colspan, rowspan: rowspan)
    block(width: g.ancho, height: g.alto, clip: clip, align(alinear, cuerpo))
  }

  let colocar(col, row, colspan: 1, rowspan: 1, alinear: top + left, clip: false, dx: 0pt, dy: 0pt, cuerpo) = {
    let g = geom(col, row, colspan: colspan, rowspan: rowspan)
    place(top + left, dx: g.x + dx, dy: g.y + dy, campo(
      col,
      row,
      colspan: colspan,
      rowspan: rowspan,
      alinear: alinear,
      clip: clip,
      cuerpo,
    ))
  }

  (
    ancho: ancho,
    alto: alto,
    columnas: columnas,
    filas: filas,
    canal_h: canal_h,
    canal_v: cv,
    campo_w: cw,
    campo_h: ch,
    _geom: geom,
    _campo: campo,
    _colocar: colocar,
  )
}

/// Geometría de un campo: (x, y, ancho, alto) desde el origen del área de texto.
#let geom(reticula, col, row, colspan: 1, rowspan: 1) = (reticula._geom)(
  col,
  row,
  colspan: colspan,
  rowspan: rowspan,
)

/// Bloque de tamaño exacto del campo, sin colocar (para usar dentro de `grid`).
#let campo(
  reticula,
  col,
  row,
  colspan: 1,
  rowspan: 1,
  alinear: top + left,
  clip: false,
  cuerpo,
) = (reticula._campo)(
  col,
  row,
  colspan: colspan,
  rowspan: rowspan,
  alinear: alinear,
  clip: clip,
  cuerpo,
)

/// Coloca contenido en un campo, en su posición absoluta dentro del área de texto.
#let colocar(
  reticula,
  col,
  row,
  colspan: 1,
  rowspan: 1,
  alinear: top + left,
  clip: false,
  dx: 0pt,
  dy: 0pt,
  cuerpo,
) = (reticula._colocar)(
  col,
  row,
  colspan: colspan,
  rowspan: rowspan,
  alinear: alinear,
  clip: clip,
  dx: dx,
  dy: dy,
  cuerpo,
)

/// Caracteres por línea que caben en una caja, a partir del avance medio
/// (mm por carácter a 10 pt). El avance lo mide el catálogo de fuentes sobre
/// una muestra neutra del idioma principal; esta función solo lo convierte en
/// caracteres por línea.
///
/// La caja se indica con `ancho` o, si no se da, con un campo de la retícula:
/// `col`, `colspan`, `row`, `rowspan`. Es una **estimación** de capacidad: el
/// avance medio no incluye kerning ni ligaduras, así que el número real de
/// caracteres de una línea compuesta puede variar unas pocas unidades.
#let caracteres_por_linea(
  reticula,
  avance,
  tamano: 10pt,
  col: 1,
  row: 1,
  colspan: 1,
  rowspan: 1,
  ancho: auto,
) = {
  let caja = if ancho != auto {
    ancho
  } else {
    geom(reticula, col, row, colspan: colspan, rowspan: rowspan).ancho
  }
  let mm_por_car = avance * (tamano / 10pt)
  caja / (mm_por_car * 1mm)
}

/// Capa de comprobación visual: campos de la retícula y/o líneas base.
/// Solo para renders de QA; su tinta no es parte del diseño.
/// - `reticula: none` omite la retícula; entonces `ancho`/`alto` son obligatorios.
/// - `base: none` omite las líneas base.
#let capa_depuracion(
  reticula: none,
  base: none,
  ancho: auto,
  alto: auto,
  tinta: rgb("#e0004d"),
  rotulos: true,
  trazo: 0.25pt,
) = {
  let w = if reticula != none { reticula.ancho } else { ancho }
  let h = if reticula != none { reticula.alto } else { alto }
  assert(w != auto and h != auto, message: "capa_depuracion: indique reticula o ancho y alto")
  let capas = ()
  if reticula != none {
    for c in range(1, reticula.columnas + 1) {
      for f in range(1, reticula.filas + 1) {
        let g = geom(reticula, c, f)
        capas.push(place(top + left, dx: g.x, dy: g.y, rect(
          width: g.ancho,
          height: g.alto,
          stroke: trazo + tinta.transparentize(35%),
        )))
        if rotulos {
          capas.push(place(top + left, dx: g.x + 1pt, dy: g.y + 1pt, text(
            size: 5pt,
            fill: tinta.transparentize(40%),
            str(c) + "," + str(f),
          )))
        }
      }
    }
  }
  if base != none {
    let n = lineas_en(h, base)
    for i in range(1, n + 1) {
      capas.push(place(top + left, dx: 0pt, dy: i * base, line(
        length: w,
        stroke: 0.2pt + tinta.transparentize(82%),
      )))
    }
  }
  block(width: w, height: h, capas.join())
}

// ---------------------------------------------------------------------------
// 4. Fotografía con proporción nativa
// ---------------------------------------------------------------------------

/// Coloca una imagen en un campo de la retícula conservando su proporción
/// nativa: se escala hasta caber en el campo (nunca se recorta, nunca se
/// deforma) y se alinea dentro de él. `ruta` es una ruta de imagen resuelta como
/// el resto de rutas de esta biblioteca: desde la raíz de Typst si empieza por
/// `/` (`"/images/foto.png"`), o relativa al archivo de la biblioteca.
///
/// Aritmética: con r = ancho_nativo / alto_nativo,
///   ancho = min(campo_ancho, campo_alto · r),  alto = ancho / r.
/// `margen` es un margen interior en los cuatro lados, no negativo: desplaza y
/// reduce el área de la imagen antes de calcular su tamaño proporcional, y no
/// puede consumir el campo entero.
///
/// Se niega a recortar o deformar salvo permiso explícito:
///   - `ajuste: "nativa"` (o "contain"): comportamiento por defecto.
///   - `ajuste: "recorte"` (o "cover"): exige `permitir_recorte: true`.
///   - `ajuste: "deformar"` (o "stretch"): exige `permitir_deformacion: true`.
///
/// Emite un `metadata` con la ruta, la proporción nativa, la colocada y el
/// campo, para que las pruebas puedan comprobar la igualdad sin leer el PDF.
///
/// `cuerpo` se coloca SOBRE la imagen ya colocada, es decir, sobre su caja
/// proporcional (no sobre el área libre del campo) y por eso exige autorización
/// explícita: la regla 2 de `SKILL.md` prohíbe texto sobre las fotografías salvo
/// petición expresa, así que sin `texto_sobre_foto: "autorizado"` la llamada
/// falla. Por defecto los pies y las leyendas van fuera de la imagen (ver `pie`).
///
#let foto(
  ruta,
  reticula,
  col: 1,
  row: 1,
  colspan: 1,
  rowspan: 1,
  alinear: top + left,
  ajuste: "nativa",
  permitir_recorte: false,
  permitir_deformacion: false,
  margen: 0pt,
  texto_sobre_foto: none,
  cuerpo: none,
) = {
  assert(margen >= 0pt, message: "foto: margen debe ser mayor o igual que 0pt")
  if cuerpo != none and texto_sobre_foto != "autorizado" {
    panic(
      "foto: por defecto no se escribe sobre las imágenes (regla 2 de SKILL.md); "
        + "para permitirlo, pase texto_sobre_foto: \"autorizado\"",
    )
  }
  let aj = if ajuste == "contain" { "nativa" } else if ajuste == "cover" {
    "recorte"
  } else if ajuste == "stretch" {
    "deformar"
  } else {
    ajuste
  }
  assert(
    aj in ("nativa", "recorte", "deformar"),
    message: "foto: ajuste debe ser \"nativa\", \"recorte\" o \"deformar\"",
  )
  if aj == "recorte" and not permitir_recorte {
    panic("foto: se ha pedido recorte (fit: \"cover\") sin permitir_recorte: true; la proporción nativa no se toca")
  }
  if aj == "deformar" and not permitir_deformacion {
    panic("foto: se ha pedido deformación (stretch) sin permitir_deformacion: true; la proporción nativa no se toca")
  }
  let g = geom(reticula, col, row, colspan: colspan, rowspan: rowspan)
  let libre_w = g.ancho - 2 * margen
  let libre_h = g.alto - 2 * margen
  assert(libre_w > 0pt and libre_h > 0pt, message: "foto: el margen interior consume el campo")
  let x_foto = g.x + margen
  let y_foto = g.y + margen

  if aj == "nativa" {
    context {
      let nat = measure(image(ruta))
      let r = nat.width / nat.height
      let bw = calc.min(libre_w, libre_h * r)
      let bh = bw / r
      let capa = block(
        width: bw,
        height: bh,
        {
          image(ruta, width: bw, height: bh, fit: "contain")
          if cuerpo != none {
            place(top + left, block(width: bw, height: bh, cuerpo))
          }
        },
      )
      let caja = block(
        width: libre_w,
        height: libre_h,
        align(alinear, capa),
      )
      let meta = metadata((
        tipo: "foto",
        ruta: str(ruta),
        ratio_nativo: r,
        ancho_nativo: nat.width,
        alto_nativo: nat.height,
        ancho: bw,
        alto: bh,
        ratio_colocado: bw / bh,
        campo: (col: col, row: row, colspan: colspan, rowspan: rowspan),
      ))
      place(top + left, dx: x_foto, dy: y_foto, caja)
      meta
    }
  } else {
    // Modos permitidos solo con permiso explícito.
    let caja = block(
      width: libre_w,
      height: libre_h,
      align(alinear, image(
        ruta,
        width: libre_w,
        height: libre_h,
        fit: if aj == "recorte" { "cover" } else { "stretch" },
      )),
    )
    place(top + left, dx: x_foto, dy: y_foto, caja)
    metadata((tipo: "foto", ruta: str(ruta), ratio_nativo: none, ajuste: aj, campo: (
      col: col,
      row: row,
      colspan: colspan,
      rowspan: rowspan,
    )))
    if cuerpo != none { place(top + left, dx: x_foto, dy: y_foto, block(width: libre_w, height: libre_h, cuerpo)) }
  }
}

/// Pie de foto: bloque de texto cuya altura se redondea al múltiplo de `base`
/// para no romper la rejilla. `alinear` fija el borde (por convención, el borde
/// exterior de la imagen o el del área de texto). Sin estilo propio: el tamaño
/// y el color los decide quien llama.
#let pie(
  texto,
  ancho: auto,
  tamano: none,
  base: none,
  alinear: left,
  separacion: none,
) = {
  let t = if tamano != none { text(size: tamano, texto) } else { texto }
  if base != none {
    // La separación superior y la altura del pie forman un módulo que se
    // redondea junto: `arriba + altura` es siempre un múltiplo exacto de la
    // línea base, aunque `separacion` no lo sea, de modo que lo que venga
    // después del pie sigue en rejilla.
    context {
      let med = measure(block(width: ancho, align(alinear, t)))
      let arriba = if separacion == none { 0pt } else { separacion }
      let total = redondear_base(med.height + arriba, base)
      let h = total - arriba
      block(width: ancho, height: h, above: arriba, below: 0pt, align(top + alinear, t))
    }
  } else {
    block(width: ancho, above: if separacion == none { 0pt } else { separacion }, align(alinear, t))
  }
}

// ---------------------------------------------------------------------------
// 5. Tablas de datos: obra y cronología
// ---------------------------------------------------------------------------

/// Tabla genérica a partir de un array de diccionarios.
///
/// `campos` es un array de diccionarios con:
///   - `clave`: nombre del campo en cada registro (obligatorio).
///   - `cabecera`: rótulo de la columna (por defecto, la clave).
///   - `ancho`: `auto`, un `fr` o una longitud (por defecto `auto`).
///   - `alinear`: alineación de la columna (por defecto `left`).
///   - `formato`: función valor → contenido (por defecto `str`).
///
/// `cabecera: false` omite la fila de rótulos; `estilo_cabecera` permite aplicar
/// peso o versalitas y, por defecto, deja el contenido sin cambios. `cifras:
/// "tabular"` usa cifras de ancho fijo para alinear verticalmente los números.
#let tabla_datos(
  datos,
  campos,
  cabecera: true,
  filete: none,
  inset: (x: 0pt, y: 0pt),
  alinear: left,
  tamano: none,
  interlineado: none,
  cifras: none,
  estilo_cabecera: it => it,
) = {
  let columnas = campos.map(c => c.at("ancho", default: auto))
  let alineaciones = campos.map(c => c.at("alinear", default: left))
  // El tamaño y el interlineado se aplican dentro de cada celda y no con reglas
  // `set`: una regla `set` dentro de un `if` no alcanza al contenido posterior,
  // así que se construye el contenido ya envuelto.
  let estilar(texto) = {
    let con_tamano = if tamano != none { text(size: tamano, texto) } else { texto }
    if interlineado != none { par(leading: interlineado, con_tamano) } else { con_tamano }
  }
  let celda(valor, campo) = {
    let texto = if valor == none or valor == "" {
      []
    } else if campo.at("formato", default: none) != none {
      campo.formato(valor)
    } else {
      str(valor)
    }
    if cifras == "tabular" { estilar(text(number-width: "tabular", texto)) } else { estilar(texto) }
  }
  let filas = datos.map(d => campos.map(c => celda(d.at(c.clave, default: none), c)))
  let cab = if cabecera {
    (table.header(..campos.map(c => estilar(estilo_cabecera(c.at("cabecera", default: c.clave))))),)
  } else {
    ()
  }
  table(
    columns: columnas,
    align: alineaciones,
    stroke: if filete == none { none } else { filete },
    inset: inset,
    ..cab,
    ..filas.flatten(),
  )
}

/// Lista de obra. `campos` por defecto: título, año, técnica, dimensiones, serie.
/// El orden y los anchos son los de la lista; los rótulos se pueden sustituir.
#let tabla_obras(
  obras,
  campos: (
    (clave: "titulo", cabecera: "Obra", ancho: 1fr, alinear: left),
    (clave: "ano", cabecera: "Año", ancho: auto, alinear: right),
    (clave: "tecnica", cabecera: "Técnica", ancho: auto, alinear: left),
    (clave: "dimensiones", cabecera: "Dimensiones", ancho: auto, alinear: left),
    (clave: "serie", cabecera: "Serie", ancho: auto, alinear: left),
  ),
  ..resto,
) = tabla_datos(obras, campos, cifras: "tabular", ..resto)

/// Cronología. `eventos` con `ano` y `hecho`; admite otros campos.
#let tabla_cronologia(
  eventos,
  campos: (
    (clave: "ano", cabecera: "Año", ancho: auto, alinear: right),
    (clave: "hecho", cabecera: "Hecho", ancho: 1fr, alinear: left),
  ),
  ..resto,
) = tabla_datos(eventos, campos, cifras: "tabular", ..resto)
