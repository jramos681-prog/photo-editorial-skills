# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.1.0] - 2026-11-10

### Added

- First public release of `maquetacion-editorial`, the collection's first
  skill: it designs and typesets photographic documents in Typst (dossier,
  portfolio, photobook, exhibition materials) from the purpose of each
  document, with nine reference documents under `references/`.
- Three command-line Python tools under
  `skills/maquetacion-editorial/scripts/`: `control_pdf.py` checks the
  produced PDF, `hoja_contactos.py` renders PDF pages to PNG and builds
  contact sheets, and `catalogo_fuentes.py` measures available font
  families. They share `configuracion.py`, which loads the project
  configuration.
- The Typst library `skills/maquetacion-editorial/typst/editorial.typ`: page
  geometry, margin canons, grid, baseline, photographs at their native aspect
  ratio, captions and work tables.
- `skills/maquetacion-editorial/config.ejemplo.md`, the template of the
  project configuration read when the skill is activated: languages, fonts and
  delivery names.
