// Beli Bryag — maquetación para pantalla. Programa: programa_v01.md; memoria: memoria_v01.md.
// Compilar desde la raíz del proyecto:
//   typst compile --root . --font-path fuentes beli_bryag/beli_bryag.typ beli_bryag/beli_bryag_v01.pdf
// Con la capa de retícula: añadir --input qa=si.
//
// Cada página coloca sus elementos en el orden de contenido_v01.md (E01…E60),
// de modo que el texto del PDF se extrae, se copia y se lee en ese orden.
#import "../.claude/skills/maquetacion-editorial/typst/editorial.typ": reticula, geom, foto, capa_depuracion
#import "contenido.typ": C, R, S

#let QA = sys.inputs.at("qa", default: "no") == "si"

// ---------------------------------------------------------------------------
// Geometría (programa §2)
// ---------------------------------------------------------------------------
#let PW = 320mm
#let PH = 200mm
#let B = 15pt                    // línea base
#let CAP = 0.66                  // altura de mayúscula de Spectral (OS/2: 660/1000)
#let C11 = CAP * 11pt            // mayúscula del cuerpo de texto (11 pt)
#let LAT = 17mm                  // márgenes laterales
#let SUP = 13mm + (B - C11)      // la mancha arranca en la línea de mayúsculas de la 1.ª línea
#let N = 31                      // líneas de la mancha
#let ALTO = (N - 1) * B + C11    // de la mayúscula de la 1.ª línea a la base de la 31.ª
#let ANCHO = PW - 2 * LAT
#let INF = PH - SUP - ALTO

// 12 columnas × 8 filas de 3 líneas. Cada campo va de la mayúscula de su
// primera línea a la base de la tercera; el canal es una línea más el resto.
#let r = reticula(
  ancho: ANCHO, alto: ALTO, columnas: 12, filas: 8,
  canal_h: 5mm, canal_v: 2 * B - C11,
)
#let xc(col) = geom(r, col, 1).x
#let wc(n) = geom(r, 1, 1, colspan: n).ancho
#let yf(row) = geom(r, 1, row).y

// ---------------------------------------------------------------------------
// Tipografía (programa §2): una sola familia, Spectral
// ---------------------------------------------------------------------------
#let TINTA = rgb("#1c1c1c")
#let GRIS = rgb("#5c5c5c")
#let FAM = "Spectral"

// Texto con la caja de línea de mayúscula a base: un bloque de n líneas mide
// (n − 1)·paso + mayúscula, y su última línea cae en su borde inferior.
#let estilo(tam, paso, peso: 400, estilo_: "normal", color: TINTA, sangria: 0pt, sangrar_todo: false, cuerpo) = {
  set text(
    font: FAM, size: tam, weight: peso, style: estilo_, fill: color, lang: "es",
    top-edge: "cap-height", bottom-edge: "baseline", number-type: "old-style",
  )
  set par(
    leading: paso - CAP * tam, spacing: paso - CAP * tam, justify: false,
    first-line-indent: (amount: sangria, all: sangrar_todo),
  )
  cuerpo
}

#let T_TEXTO = 11pt
#let T_PIE = 8.5pt
#let T_CITA = 16pt
// `sigue: true` para un párrafo que continúa otro bloque de la misma columna
// (lleva sangría, como cualquier párrafo que no abre).
#let texto(cuerpo, sigue: false) = estilo(T_TEXTO, B, sangria: 1em, sangrar_todo: sigue, cuerpo)
#let pie_estilo(cuerpo) = estilo(T_PIE, 11pt, color: GRIS, cuerpo)
#let cita_estilo(cuerpo) = estilo(T_CITA, 1.5 * B, peso: 300, estilo_: "italic", cuerpo)
#let seccion_estilo(cuerpo) = estilo(21pt, 2 * B, peso: 300, cuerpo)

// Desplazamiento para que la primera base de un cuerpo `tam` caiga en la
// primera base de la rejilla (que está a C11 del borde del campo).
#let dy_base(tam) = C11 - CAP * tam

// ---------------------------------------------------------------------------
// Colocación
// ---------------------------------------------------------------------------
// Coloca `cuerpo` con su esquina superior (línea de mayúsculas) en (x, y) de la mancha.
#let en(x, y, ancho, cuerpo) = place(top + left, dx: x, dy: y, block(width: ancho, cuerpo))
#let alto(ancho, cuerpo) = measure(block(width: ancho, cuerpo)).height

// Texto en columna: arranca en la cabeza de la mancha (o en `y`, que debe ser
// una línea de mayúsculas de la rejilla).
#let columna(col, cuerpo, y: 0pt, colspan: 4, sigue: false) = en(xc(col), y, wc(colspan), texto(cuerpo, sigue: sigue))

// Segundo bloque de una columna partida por una foto: empieza una línea base
// por debajo del primero, con la misma separación que entre párrafos. El
// `par` explícito hace falta para que Typst aplique la sangría: un bloque con
// un solo párrafo sin salto no cuenta como párrafo.
#let tras(col, previo, cuerpo, colspan: 4, y0: 0pt) = context {
  let h = alto(wc(colspan), texto(previo))
  columna(col, par(cuerpo), y: y0 + h + B - C11, colspan: colspan, sigue: true)
}

// Rótulo de sección con su mayúscula en la cabeza del campo; el texto, tres
// líneas más abajo y otra vez en rejilla.
#let rotulo(col, titulo, colspan: 4) = en(xc(col), 0pt, wc(colspan), seccion_estilo(titulo))
#let Y_TRAS_ROTULO = 3 * B

// Bloque cuya última base cae en `ybase` (por defecto, la base de la mancha).
#let abajo(x, ancho, cuerpo, ybase: ALTO) = context {
  en(x, ybase - alto(ancho, cuerpo), ancho, cuerpo)
}

// Citas de testimonio, con la comilla de apertura colgada fuera de la medida
// (Bringhurst, puntuación colgante).
#let cita_arriba(x, ancho, cuerpo, y: 0pt) = context {
  let comilla = measure(cita_estilo[“]).width
  en(x - comilla, y, ancho + comilla, cita_estilo(cuerpo))
}
#let cita_abajo(x, ancho, cuerpo, ybase: ALTO) = context {
  let comilla = measure(cita_estilo[“]).width
  let h = alto(ancho + comilla, cita_estilo(cuerpo))
  en(x - comilla, ybase - h, ancho + comilla, cita_estilo(cuerpo))
}

// Pies. Debajo de la foto: primera base una línea por debajo, medida de 5
// columnas como máximo. Al lado: última base en la base de la foto.
#let pie_debajo(x, yfoto, ancho, cuerpo) = en(x, yfoto + B - CAP * T_PIE, calc.min(ancho, wc(5)), pie_estilo(cuerpo))
#let pie_al_lado(x, ancho, cuerpo, ybase: ALTO) = abajo(x, ancho, pie_estilo(cuerpo), ybase: ybase)

// Foto en un campo con su proporción nativa (editorial.typ) y su geometría real.
#let geo_foto(id, col, row, colspan, rowspan, alinear) = {
  let g = geom(r, col, row, colspan: colspan, rowspan: rowspan)
  let k = R.at(id)
  let w = calc.min(g.ancho / 1mm, g.alto / 1mm * k) * 1mm
  let h = w / k
  let x = if alinear.x == right { g.x + g.ancho - w } else if alinear.x == center { g.x + (g.ancho - w) / 2 } else { g.x }
  let y = if alinear.y == bottom { g.y + g.alto - h } else { g.y }
  (x: x, y: y, ancho: w, alto: h)
}
#let poner_foto(id, col, row, colspan, rowspan, alinear) = foto(
  C.at(id), r, col: col, row: row, colspan: colspan, rowspan: rowspan, alinear: alinear,
)
// Lámina a sangre a todo el alto de la página, pegada al borde izquierdo o derecho.
#let a_sangre(id, lado) = {
  let w = PH * R.at(id)
  let dx = if lado == left { -LAT } else { ANCHO + LAT - w }
  place(top + left, dx: dx, dy: -SUP, image(C.at(id), height: PH))
}

// Folio: número de página en el margen inferior, a la derecha de la mancha,
// dos líneas por debajo de la última base.
#let folio(n) = place(top + left, dx: 0pt, dy: ALTO + 2 * B - CAP * 8pt, block(width: ANCHO, align(right, estilo(8pt, B, color: GRIS, str(n)))))

#let depuracion = if QA { capa_depuracion(reticula: r) } else { none }

#set document(title: "Beli Bryag: la incertidumbre de vivir sobre un tajo de carbón", author: "Jesús Ramos Martín")
#set page(width: PW, height: PH, margin: (left: LAT, right: LAT, top: SUP, bottom: INF), fill: white)

#let pagina(n, folio_: true, cuerpo) = {
  cuerpo
  if folio_ { folio(n) }
  if QA { place(top + left, depuracion) }
  pagebreak(weak: true)
}

// Titular con cortes de línea fijados sin tocar las palabras: se reparte la
// cadena original por posiciones de palabra.
#let cortes(cadena, grupos) = {
  let p = cadena.split(" ")
  let lineas = ()
  let i = 0
  for n in grupos {
    lineas.push(p.slice(i, i + n).join(" "))
    i += n
  }
  assert(i == p.len(), message: "cortes: los grupos no cubren todas las palabras")
  lineas.join(linebreak())
}

// ---------------------------------------------------------------------------
// 1. Portada: F01 a sangre por la izquierda (excepción declarada)
// ---------------------------------------------------------------------------
#pagina(1, folio_: false)[
  #a_sangre("E01", left)
  #pie_al_lado(xc(8), wc(3), C.E02)
  #en(xc(8), 0pt, wc(5), estilo(36pt, 3 * B, peso: 300, cortes(S.E03, (2, 2, 3, 4))))
  #en(xc(8), yf(4), wc(5), texto[Jesús Ramos Martín, 2025])
  #en(xc(8), yf(5) + dy_base(14pt), wc(5), estilo(14pt, 20pt, C.E04))
]

// ---------------------------------------------------------------------------
// 2. E05 · F02 · E07 · E08 — columna a la izquierda, foto principal a la derecha
// ---------------------------------------------------------------------------
#pagina(2)[
  #columna(1, C.E05)
  #poner_foto("E06", 5, 1, 8, 8, top + right)
  #pie_al_lado(xc(2), wc(3), C.E07)
  #tras(1, C.E05, C.E08)
]

// ---------------------------------------------------------------------------
// 3. E09 · F03 · E11 · E12 — apertura de «Beli Bryag»: foto a la izquierda
// ---------------------------------------------------------------------------
#pagina(3)[
  #rotulo(8, C.E09)
  #poner_foto("E10", 1, 1, 6, 8, top + left)
  #let f = geo_foto("E10", 1, 1, 6, 8, top + left)
  #pie_debajo(f.x, f.y + f.alto, f.ancho, C.E11)
  #columna(8, C.E12, y: Y_TRAS_ROTULO)
]

// ---------------------------------------------------------------------------
// 4. E13 · F04 · E15 · E16 — texto a la izquierda; horizontal y cita a la derecha
// ---------------------------------------------------------------------------
#pagina(4)[
  #columna(1, C.E13)
  #poner_foto("E14", 5, 1, 8, 6, top + right)
  #let f = geo_foto("E14", 5, 1, 8, 6, top + right)
  #pie_debajo(f.x, f.y + f.alto, f.ancho, C.E15)
  #cita_abajo(f.x, wc(5), C.E16)
]

// ---------------------------------------------------------------------------
// 5. E17 · E18 · F05 · E20 — apertura de «Sus habitantes»
// ---------------------------------------------------------------------------
#pagina(5)[
  #rotulo(1, C.E17)
  #columna(1, C.E18, y: Y_TRAS_ROTULO)
  #poner_foto("E19", 6, 1, 7, 8, top + right)
  #pie_al_lado(xc(5), wc(2), C.E20)
]

// ---------------------------------------------------------------------------
// 6. E21 · F06 · E23 · E24 — foto a la izquierda; texto y cita a la derecha
// ---------------------------------------------------------------------------
#pagina(6)[
  #columna(8, C.E21)
  #poner_foto("E22", 1, 1, 7, 7, top + left)
  #let f = geo_foto("E22", 1, 1, 7, 7, top + left)
  #pie_debajo(f.x, f.y + f.alto, f.ancho, C.E23)
  #cita_abajo(xc(8), wc(4), C.E24)
]

// ---------------------------------------------------------------------------
// 7. E25 · F07 · E27 · E28 — cita y texto a la izquierda; foto a la derecha
// ---------------------------------------------------------------------------
#pagina(7)[
  #cita_arriba(xc(1), wc(4), C.E25)
  #poner_foto("E26", 6, 1, 7, 8, top + right)
  #pie_al_lado(xc(4), wc(2), C.E27)
  #context {
    // Primera base del texto en la rejilla, al menos dos líneas por debajo de
    // la última base de la cita.
    let comilla = measure(cita_estilo[“]).width
    let ultima = alto(wc(4) + comilla, cita_estilo(C.E25))
    let k = calc.ceil((ultima + 2 * B - C11) / B)
    columna(1, C.E28, y: k * B)
  }
]

// ---------------------------------------------------------------------------
// 8. F08 · E30 · E31 — retrato del nieto, con la cita al lado
// ---------------------------------------------------------------------------
#pagina(8)[
  #poner_foto("E29", 1, 2, 9, 6, top + left)
  #let f = geo_foto("E29", 1, 2, 9, 6, top + left)
  #pie_debajo(f.x, f.y + f.alto, f.ancho, C.E30)
  #cita_abajo(xc(10), wc(3), C.E31, ybase: f.y + f.alto)
]

// ---------------------------------------------------------------------------
// 9. F09 · E33 · E34 — horizontal a la izquierda; texto a la derecha
// ---------------------------------------------------------------------------
// F09 se reduce a 180 mm de ancho (excepción declarada) para dejar aire entre
// la foto y la columna y para que quede por debajo del retrato de la pág. 8.
#pagina(9)[
  #let w = 180mm
  #let h = w / R.E32
  #place(top + left, dx: 0pt, dy: 0pt, image(C.E32, width: w))
  #pie_debajo(0pt, h, w, C.E33)
  #columna(9, C.E34)
]

// ---------------------------------------------------------------------------
// 10. F10 · E36 — lámina: retrato del abuelo
// ---------------------------------------------------------------------------
#pagina(10)[
  #poner_foto("E35", 4, 1, 6, 8, top + left)
  #pie_al_lado(xc(10), wc(3), C.E36)
]

// ---------------------------------------------------------------------------
// 11. E37 · E38 · F11 · E40 — texto a la izquierda; foto a la derecha
// ---------------------------------------------------------------------------
#pagina(11)[
  #columna(1)[#C.E37

    #C.E38]
  #poner_foto("E39", 6, 1, 7, 8, top + right)
  #pie_al_lado(xc(5), wc(2), C.E40)
]

// ---------------------------------------------------------------------------
// 12. E41 · E42 · F12 · E44 — apertura de «Transición energética»: F12 a sangre
// por la izquierda, eco de la portada (excepción declarada)
// ---------------------------------------------------------------------------
#pagina(12)[
  #rotulo(8, C.E41)
  #columna(8, C.E42, y: Y_TRAS_ROTULO)
  #a_sangre("E43", left)
  #pie_al_lado(xc(8), wc(4), C.E44)
]

// ---------------------------------------------------------------------------
// 13. E45 · F13 · E47 · E48 — texto a la izquierda; horizontal a la derecha
// ---------------------------------------------------------------------------
#pagina(13)[
  #columna(1, C.E45)
  #poner_foto("E46", 5, 1, 8, 6, top + right)
  #let f = geo_foto("E46", 5, 1, 8, 6, top + right)
  #pie_debajo(f.x, f.y + f.alto, f.ancho, C.E47)
  #tras(1, C.E45, C.E48)
]

// ---------------------------------------------------------------------------
// 14. E49 · F14 · E51 · E52 — foto a la izquierda; texto a la derecha
// ---------------------------------------------------------------------------
#pagina(14)[
  #columna(7, C.E49)
  #poner_foto("E50", 1, 1, 6, 8, top + left)
  #pie_al_lado(xc(7), wc(4), C.E51)
  #tras(7, C.E49, C.E52)
]

// ---------------------------------------------------------------------------
// 15. E53 · E54 · E55 · F15 · E57 · E58 — apertura de «Conclusión»
// ---------------------------------------------------------------------------
#let E54_55 = [#C.E54

  #C.E55]
#pagina(15)[
  #rotulo(1, C.E53)
  #columna(1, E54_55, y: Y_TRAS_ROTULO)
  #poner_foto("E56", 5, 1, 8, 7, top + right)
  #let f = geo_foto("E56", 5, 1, 8, 7, top + right)
  #pie_debajo(f.x, f.y + f.alto, f.ancho, C.E57)
  #tras(1, E54_55, C.E58, y0: Y_TRAS_ROTULO)
]

// ---------------------------------------------------------------------------
// 16. F16 · E60 — cierre: lámina vertical a sangre por la derecha (excepción declarada)
// ---------------------------------------------------------------------------
#pagina(16, folio_: false)[
  #a_sangre("E59", right)
  #pie_al_lado(xc(5), wc(3), C.E60)
]
