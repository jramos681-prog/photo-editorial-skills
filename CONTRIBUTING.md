# Contributing

Issues and pull requests are welcome.

## Language

The skills are written in Spanish: `SKILL.md`, the documents under
`references/` and the example configuration. Repository documentation, such as
this file and `CHANGELOG.md`, is written in English.

## Running the tests

The suite lives in `tests/`, builds its own fixtures and needs no material from
outside the repository. From the repository root:

```sh
python -m pip install -r tests/requirements.txt
python -m pytest tests
```

Typst must be on `PATH`: the tests compile the library under
`skills/maquetacion-editorial/typst/` with the version installed locally.

## Licenses

- The code under `skills/*/scripts/` and `skills/*/typst/` is licensed under
  the MIT License; see `LICENSE`.
- Original text of the skills and repository documentation is licensed under
  CC BY 4.0; third-party material identified in `NOTICE` remains under its
  upstream license. See `LICENSE-docs`.
- Keep the third-party notices in `NOTICE` when you change a file they cover.

## Example photographs

The photographs in `examples/` are the author's work, with all rights
reserved. They are not licensed for reuse: do not copy them into a pull
request, a test fixture or any other work.
