# Developing this pack

General rules for all packs are in the repository's [CONTRIBUTING.md](../../CONTRIBUTING.md). This page covers what is specific to the CAMT and TWIST Parser. The most valuable contribution is a **new example of a real-world layout**, anonymised.

## Ways to help

- **Send an anonymised sample** of a camt.086 or TWIST file that parses badly. Use the "Format or bank support request" issue template.
- **Report a bug** with the smallest XML that reproduces it.
- **Improve the docs**, especially notes on how particular banks use the formats.
- **Send a pull request** for a fix or a feature from the roadmap below.

## Anonymising a statement

Replace names, account numbers, IBANs, BICs, references and amounts. Keep element names, nesting, attributes and the pattern of repeated elements. Never commit or attach real client data.

## Development setup

No dependencies are needed.

```bash
git clone https://github.com/sa-nishad/treasuryease.git
cd treasuryease/packs/camt-twist-parser
python -m unittest discover -s tests -v
```

Open `web/index.html` in a browser to work on the app. There is no build step.

## Two implementations, one algorithm

`web/index.html` (JavaScript) and `src/camt_twist_parser/core.py` (Python) implement the same algorithm. If you change how rows, columns or labels are produced, change both and make sure the output still matches:

1. Run the unit tests.
2. Open the sample files in the web app and compare the CSV from the Export tab with `samples/expected/*.csv`.

Sample files: `samples/example-*.xml` follow real element structure with invented values (regenerate them with `samples/make_samples.py`). `samples/minimal-*.xml` are tiny files for focused tests.

If you change the expected output on purpose, regenerate the golden files and explain why in the pull request.

## Pull request checklist

- Tests pass and cover the change.
- No real statement data in samples, tests or screenshots.
- Both implementations updated when the algorithm changes.
- This pack's `CHANGELOG.md` has a line for user-visible changes.

## Roadmap ideas

- Test against more camt.086 versions and bank-specific TWIST layouts.
- Command-line option to write one output file per input file.
- Column mapping files (rename, reorder, drop columns).
- Excel (.xlsx) export.
- JavaScript tests that run the web app's parser in CI.
- Support for other ISO 20022 statement messages.

## Conduct

Be kind and assume good faith. See [CODE_OF_CONDUCT.md](../../CODE_OF_CONDUCT.md).
