# Roadmap

These are ideas, not promises. Open an issue with the "Pack idea" template to discuss one, or to propose another.

## Available

| Pack | Notes |
| --- | --- |
| CAMT and TWIST Parser | Version 0.1. Needs more real-world layouts, so send anonymised samples. |

## Ideas

| Pack | What it would do | Builds on |
| --- | --- | --- |
| Statement to CSV | Flatten camt.053 and MT940 account statements into clean CSV or JSON. | The parser's row detection and column naming |
| Recon Diff | Compare two extracts by key with tolerances and list what is missing, extra or different. Useful for migration and load checks. | |
| Payment File Checker | Validate pain.001 files before they go to the bank: IBAN and BIC format, control sums, duplicates. | |
| Fee Analytics | Trend bank fees and unit prices month on month from parsed statements and flag changes. | CAMT and TWIST Parser output |
| FX Rates Loader | Turn published reference rates into load-ready CSV for a treasury system. | |
| Load File Builder | Validate a spreadsheet and write it as a load file for static data in a treasury system. | |

## How packs are chosen

1. The task is repetitive, rule-based and done by hand today.
2. It can be done on a user's machine with plain files.
3. Output can be checked against an independent source.
4. It can be shown with synthetic data.

## Not in scope

Anything that needs to hold credentials, move money or connect to a bank. Packs prepare, check and explain data. They do not execute payments.
