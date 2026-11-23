# Security and data handling

## Your data

Packs are designed to run on your computer. Browser apps parse files locally and do not upload them. The only network request a page makes is the optional Google Fonts stylesheet; remove that `<link>` for a fully offline copy.

## Handling real statements

Bank files and treasury extracts are confidential. When you report a bug or request support:

- Replace names, account numbers, IBANs, BICs, references and amounts.
- Keep the element names and the nesting, because packs depend on them.
- Check the file name as well as the contents.
- Never attach an unmodified file to an issue or pull request.

Maintainers: set the repository variable `HYGIENE_DENYLIST` (Settings, Secrets and variables, Actions, Variables) to a comma-separated list of client, bank and system names that must never appear. The pipeline fails if one does.

## Reporting a vulnerability

Please do not open a public issue for a security problem. Use GitHub's private vulnerability reporting (Security tab, Report a vulnerability), or contact the maintainer privately.

## XML safety

Python packs use the standard library XML parser. Do not point them at untrusted XML from the internet without reading the Python documentation on XML vulnerabilities. Browser apps use the browser's own XML parser.
