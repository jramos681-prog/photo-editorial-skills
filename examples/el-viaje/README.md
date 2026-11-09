# El viaje: four models, with and without the skill

*El viaje* is a photographic project by the author: 23 photographs and their texts, 64 blocks in a fixed sequence. It was laid out eight times for on-screen reading, page by page: four models, each tested with and without the skill, using identical material and the exact same prompt.

## The prompt

The exact same message across all eight sessions:

> Quiero transformar *El viaje* (la carpeta con los textos y las fotos del proyecto) en una obra bien maquetada. El contenido ha de ser invariable y no puede cambiarse bajo ningún concepto: ni el texto, ni las fotos, ni su orden. Es para verlo en pantalla, página a página. El objetivo es tener un documento en el que pueda mostrar el trabajo de la mejor manera posible; el documento debe adaptarse al contenido.

> *English translation:*
> "I want to turn *El viaje* (the folder with the project's texts and photos) into a well-designed piece. The content must stay unchanged under all circumstances: neither the text, nor the photos, nor their order. It is meant to be viewed on screen, page by page. The goal is to have a document where I can show the work in the best possible way; the document must adapt to the content."

## Results

| Model | Score without skill | Score with skill | Cost without skill (USD) | Cost with skill (USD) | Cost with / without |
|---|---|---|---|---|---|
| Sol 6.1 | 3 | 7 | 0.39 | 1.72 | ×4.41 |
| Opus 5.5 | 3 | 6 | 1.79 | 5.66 | ×3.16 |
| Gemini 3.8 Flash | 4 | 5 | 0.90 | 1.07 | ×1.19 |
| DeepSeek V4.1 Flash | 3 | 2 | 0.19 | 0.22 | ×1.16 |

![Session cost versus author score, with and without skill](img/coste-nota.svg)

The score is the author's entirely subjective assessment on a scale from 0 to 10. It was conducted blindly: the author evaluated the eight documents without knowing which model created each one or whether the skill had been used.

The cost represents the session up to the evaluated delivery, as recorded by the agent. Comparing cost is only meaningful between the same model with and without the skill, since each provider sets their own pricing.

## Four pages from each document

This is the best way to compare. In each case, four representative pages of the document are shown.

### Sol 6.1

Without skill:

![Sol 6.1 without skill, four pages](img/sol-sin-4paginas.jpg)

With skill:

![Sol 6.1 with skill, four pages](img/sol-con-4paginas.jpg)

### Opus 5.5

Without skill:

![Opus 5.5 without skill, four pages](img/opus-sin-4paginas.jpg)

With skill:

![Opus 5.5 with skill, four pages](img/opus-con-4paginas.jpg)

### Gemini 3.8 Flash

Without skill:

![Gemini 3.8 Flash without skill, four pages](img/gemini-sin-4paginas.jpg)

With skill:

![Gemini 3.8 Flash with skill, four pages](img/gemini-con-4paginas.jpg)

### DeepSeek V4.1 Flash

Without skill:

![DeepSeek V4.1 Flash without skill, four pages](img/deepseek-sin-4paginas.jpg)

With skill:

![DeepSeek V4.1 Flash with skill, four pages](img/deepseek-con-4paginas.jpg)

## The same page across all eight documents

The page where the same content block falls in each document. Click on any image to view it at 1600 px.

| | Sol 6.1 | Opus 5.5 | Gemini 3.8 Flash | DeepSeek V4.1 Flash |
|---|---|---|---|---|
| **Without skill** | <a href="img/sol-sin-pagina.jpg"><img src="img/sol-sin-pagina.jpg" width="180" alt="Sol 6.1 without skill"></a> | <a href="img/opus-sin-pagina.jpg"><img src="img/opus-sin-pagina.jpg" width="180" alt="Opus 5.5 without skill"></a> | <a href="img/gemini-sin-pagina.jpg"><img src="img/gemini-sin-pagina.jpg" width="180" alt="Gemini 3.8 Flash without skill"></a> | <a href="img/deepseek-sin-pagina.jpg"><img src="img/deepseek-sin-pagina.jpg" width="180" alt="DeepSeek V4.1 Flash without skill"></a> |
| **With skill** | <a href="img/sol-con-pagina.jpg"><img src="img/sol-con-pagina.jpg" width="180" alt="Sol 6.1 with skill"></a> | <a href="img/opus-con-pagina.jpg"><img src="img/opus-con-pagina.jpg" width="180" alt="Opus 5.5 with skill"></a> | <a href="img/gemini-con-pagina.jpg"><img src="img/gemini-con-pagina.jpg" width="180" alt="Gemini 3.8 Flash with skill"></a> | <a href="img/deepseek-con-pagina.jpg"><img src="img/deepseek-con-pagina.jpg" width="180" alt="DeepSeek V4.1 Flash with skill"></a> |

## Contact sheets

All pages of each document, shown at the same thumbnail size across all sheets.

<details>
<summary>Sol 6.1</summary>

Without skill:

![Sol 6.1 without skill, contact sheet](img/sol-sin-contactos.jpg)

With skill:

![Sol 6.1 with skill, contact sheet](img/sol-con-contactos.jpg)

</details>

<details>
<summary>Opus 5.5</summary>

Without skill:

![Opus 5.5 without skill, contact sheet](img/opus-sin-contactos.jpg)

With skill:

![Opus 5.5 with skill, contact sheet](img/opus-con-contactos.jpg)

</details>

<details>
<summary>Gemini 3.8 Flash</summary>

Without skill:

![Gemini 3.8 Flash without skill, contact sheet](img/gemini-sin-contactos.jpg)

With skill:

![Gemini 3.8 Flash with skill, contact sheet](img/gemini-con-contactos.jpg)

</details>

<details>
<summary>DeepSeek V4.1 Flash</summary>

Without skill:

![DeepSeek V4.1 Flash without skill, contact sheet](img/deepseek-sin-contactos.jpg)

With skill:

![DeepSeek V4.1 Flash with skill, contact sheet](img/deepseek-con-contactos.jpg)

</details>

## How it was done

- **Date and environment:** November 9, 2026, using the Oh My Pi terminal agent (version 18.18.3).
- **Reasoning effort:** high on Opus 5.5, Sol 6.1, and Gemini 3.8 Flash; maximum on DeepSeek V4.1 Flash.
- **Material:** eight clean folders with identical contents: the 23 photographs and a single file containing texts and photos in sequence, with no prior layout.
- **Skills:** all eight folders include the [`typst`](https://github.com/lucifer1004/claude-skill-typst) skill; the four "with skill" folders also include `maquetacion-editorial`. The agent has other general-purpose skills installed, identical across all eight sessions and unrelated to layout.
- **One run per case.** The same model produces different results across separate executions.

### The author's responses

The author's verbatim responses in each session:

- **Sol 6.1 with skill:**
  - design program (programa): «aprobado» ("approved");
  - sample pages (muestras): «aprobadas» ("approved");
  - delivery (entrega): «aprobada» ("approved").

  No adjustments were requested at any approval gate.
- **Opus 5.5 with skill:** a single form, with approval «si» ("yes"), background «blanco» ("white"), apostrophe «tipografico» ("typographic"), and no comments.
- **Gemini 3.8 Flash with skill, DeepSeek V4.1 Flash with skill, and the four sessions without skill:** asked no questions.
