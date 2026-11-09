# photo-editorial-skills

Skills for an AI agent to lay out image-heavy documents (portfolios, dossiers, photobooks, exhibition materials) with editorial judgment, deriving the design directly from the material itself, without templates.

The first skill in the collection is **`maquetacion-editorial`**. The next will be `secuencia-fotografica`, for selecting and sequencing photographs prior to layout.

## Why this exists

Photographers, architects, and other professionals who regularly rely on portfolios, dossiers, and other image-heavy documents frequently run into the challenge of laying them out. Producing good layout demands considerable time and in-depth knowledge, yet it is all too common to have neither that time nor that expertise.

Faced with this situation, turning directly to AI agents to handle the layout does not solve the problem. Their output is typically of very low quality: they default to cream backgrounds, ignore the grid, neglect alignments, or choose poor typefaces and mismatched type pairings. The result is usually a homogeneous look that "reeks of AI", a layout that simply is not an option for any document intended for presentation.

The skill's knowledge base draws directly on classic books on typography and page layout, especially canonical references by Bringhurst, Tschichold, and Müller-Brockmann.

Furthermore, the tool is not merely a compilation of aesthetic rules. It implements a workflow designed to shape the layout according to the author's intent, ensuring the final document communicates what its creator intended.

Obviously, this tool is not a substitute for a skilled layout designer, who remains indispensable for work demanding deep editorial judgment. However, it will be a great help in improving the quality of everyday documents that might otherwise never receive proper layout.

## What it does and does not do

The skill designs and typesets the document in [Typst](https://typst.app) and delivers a reviewed PDF. Every decision (format, grid, typography, size and placement of each photo, pacing) is derived from the material, the document's purpose, and user input, with written rationales provided for each choice. It does not try to impose a predefined style.

There are things the skill never does, because they belong to the author:

- **It does not alter the sequence.** If the photos arrive in an approved order, they are not reordered, removed, or added to.
- **It does not crop or distort photographs**, and does not place text over them unless the author asks for it.
- **It does not rewrite the text.** Typos and writing issues are flagged; they are not corrected autonomously.
- **It does not invent data**, measurements, or requirements. Anything unconfirmed is marked as pending verification.
- **It never assumes approval.** Approvals belong to the author and must be explicit.

## How it works

1. **Design program (programa).** Before laying out anything, the agent drafts the program for the document: what it is for, who will read it and in what setting, what constraints it has, and what tone it should convey. The parameters follow from this, each with its rationale. *First approval gate:* the author approves it.
2. **System.** Format and medium, grid, image treatment, and typographic system, supported by reference literature (see below).
3. **Sample.** The agent typesets 2 to 4 pages representing the document's page types. *Second approval gate:* the author approves them before the rest is composed.
4. **Production.** Typesetting in Typst on the grid, using a custom library (`editorial.typ`) that calculates margins, grid, and baseline, placing each photo at its native aspect ratio.
5. **Evaluation.** Automated PDF inspection (pages, bleed/trim, fonts, characters, resolution, file size, metadata, anonymity, line length, safety margins), contact sheets to view the whole document, a checklist of AI-generated design tells to justify or remove, and verification of the program against the built document. *Third approval gate:* the author approves delivery.

At each approval gate, the agent pauses and gives the exact path of what needs review. For small pieces (one or two pages, up to three images), there is a short track with a single approval gate.

### Foundations

The criteria come from six reference books: Bringhurst (*The Elements of Typographic Style*), Tschichold (*The Form of the Book*), Müller-Brockmann (*Grid Systems in Graphic Design*), Gerstner (*Designing Programmes*), Parr and Badger (*The Photobook: A History*), and Read (*Exhibiting Photography*). Each criterion includes its citation and its nature: skill rule, technical constraint, heuristic, or aesthetic preference, so the agent understands how strictly each applies. The full list is in [BIBLIOGRAPHY.md](BIBLIOGRAPHY.md).

Some parts of the text are based on skills by other authors; provenance, licenses, and notices are in [NOTICE](NOTICE).

### Language

The skill is written in Spanish. The agent speaks with the user in the user's language and delivers working documents (program, decision log, issue report) in that language. For the laid-out document, the skill includes built-in data for Spanish and English (characters, conventions, and labels); other languages can be declared in the configuration.

## Installation

### Requirements

- [Typst](https://typst.app) 0.15.1 or later.
- Python 3.10 or later, with PyMuPDF, Pillow, and fontTools. PyYAML is optional.
- The [`typst`](https://github.com/lucifer1004/claude-skill-typst) skill by lucifer1004 for Typst syntax. While `maquetacion-editorial` makes the design decisions, the `typst` skill explains how to write the code.

```
pip install pymupdf pillow fonttools pyyaml
```

### As a Claude Code plugin

```
/plugin marketplace add jramos681-prog/photo-editorial-skills
/plugin install photo-editorial-skills@photo-editorial-skills
```

### Manual install

Copy the `skills/maquetacion-editorial` folder into your agent's skills directory: for example, `.claude/skills/` inside the project, or `~/.claude/skills/` across all projects.

## Configuration

The skill works out of the box with zero configuration. If you want to specify language, fonts, or delivery filenames, create `maquetacion/config.md` in the project root based on [`config.ejemplo.md`](skills/maquetacion-editorial/config.ejemplo.md). There are three levels:

- **Zero configuration:** uses system-installed fonts and those packaged with Typst.
- **Custom fonts:** any fonts placed in the project's `fuentes/` folder.
- **Preferences:** preferred and avoided font families, license notes, and custom rules written in plain language.

For each project, the agent generates a catalog of available fonts, categorizing those suitable for body text, those fit only for headings, and those unsuitable, choosing only among the viable ones.

## Examples

- **[Beli Bryag](examples/beli-bryag/)**: the photojournalism story "Beli Bryag: The Uncertainty of Living on a Coal Pit" (16 photographs and around 1,700 words), laid out for on-screen reading by the same model using the exact same prompt, both with and without the skill, alongside the author's original layout. Includes the program, the decision log, and the quality control report from the version with the skill.
- **[El viaje](examples/el-viaje/)**: the same prompt laid out eight times across four models (Opus 5.5, Sol 6.1, Gemini 3.8 Flash, and DeepSeek V4.1 Flash), each tested with and without the skill. Includes the author's score for each document in a blind review, the cost of each session, four sample pages from each document, and their contact sheets.

Regarding the comparison: sessions started from clean folders, with identical material, the same prompt, and the same model within each pair; only the presence of the skill varied. There are three caveats. There is only one run per case, and the same model produces different outputs on each run. In sessions with the skill, the author responds at approval gates; in *El viaje*, his verbatim answers are published alongside each session so you can see what he decided versus what the model decided. And in *El viaje*, the score is the author's subjective rating, albeit done blindly: he did not know which model produced which document or whether the skill was used.

## Known limitations

- Typst does not output PDF/X or crop marks, and its CMYK export lacks embedded color profiles. If a commercial printer requires them, the skill warns you so you can post-process the output with another tool.
- The skill guides decisions; it does not guarantee perfection. The agent can make mistakes, which is why the three approval gates belong to the author.

## Licenses

- **Code** (scripts and `editorial.typ`): MIT, see [LICENSE](LICENSE).
- **Documentation and text** (the skill, its reference files, and documentation): CC BY 4.0, see [LICENSE-docs](LICENSE-docs). Direct book quotations belong to their respective authors and publishers and fall outside this license.
- **Third-party material:** under its original license, see [NOTICE](NOTICE).
- **Example photographs:** work of Jesús Ramos Martín, all rights reserved. They are not covered by any of the licenses above and cannot be reused outside this repository without explicit permission.

## Author

Jesús Ramos Martín.
