# Changelog: CAMT and TWIST Parser pack

## 0.1.0

First public release.

- Browser app: drag and drop camt.086 and TWIST XML, table view with filter, sort and column chooser, summary totals by currency, structure tree, CSV and JSON export.
- Python command-line tool with the same parsing logic and no dependencies.
- Automatic row detection with manual override.
- Header and statement fields repeated on every row.
- Optional signed amounts from the credit/debit indicator.
- Unit tests and golden output files.
- Checked against real camt.086.001.01, camt.086.001.02 and TWIST 3.1 files: service lines are preferred over compensation lines, currency is found as an attribute or a sibling field, `Sgn` is understood, amounts such as `.99` are accepted, and totals ignore header-level amounts.
- Postal address fields are skipped unless requested.
