# Launch checklist (GitHub)

## Before you publish

- [ ] **Confirm you are free to publish it.** If any of this was written or tested while working for a client or employer, read the IP and confidentiality clauses in your contract, or ask. Never publish anything derived from a client's real statements, confidential field names or internal layouts.
- [ ] Check the name (see [NAMING.md](NAMING.md)).
- [ ] Confirm the copyright line in `LICENSE`.
- [ ] Run `python tools/check_packs.py` and `python tools/run_tests.py`.
- [ ] Search the repository for real data: bank names, client or company names, BICs, IBANs, account numbers, long reference numbers. Check file names too. Do not publish any file that came from a real statement, even one you believe is anonymised, unless you have re-read every line.
- [ ] Open each browser app locally and try the sample files.

## Create the repository

1. On GitHub click **+**, then **New repository**.
2. **Repository name:** `treasuryease`. **Description:** Open source automation packs that make treasury processing easy. **Public.**
3. Do **not** add a README, .gitignore or licence; the project already has them.
4. Push:

```bash
cd treasuryease
git init -b main
git add .
git commit -m "Initial release"
git remote add origin https://github.com/sa-nishad/treasuryease.git
git push -u origin main
```

GitHub asks for a username and a password. Use a **personal access token** as the password (Settings, Developer settings, Personal access tokens), or sign in with GitHub CLI (`gh auth login`).

## Repository settings

- **About (top right of the repo page):** add topics `treasury`, `iso20022`, `camt-086`, `twist`, `bank-fees`, `csv`, `json`, `fintech`, `python`, `automation`.
- **Pages:** Settings, Pages, Source: **GitHub Actions**. Do this before the first push, or re-run the workflow afterwards. The site appears at `https://sa-nishad.github.io/treasuryease/`.
- **Branch protection:** Settings, Branches, add a rule for `main`: require a pull request and require the `check` and `test` jobs to pass.
- **Hygiene variable:** Settings, Secrets and variables, Actions, Variables, add `HYGIENE_DENYLIST` with a comma-separated list of client, bank and system names that must never appear.
- **Security:** Settings, Code security, enable private vulnerability reporting.
- **Issues:** the three templates in `.github/ISSUE_TEMPLATE/` appear automatically.
- **Release:** Releases, Draft a new release, tag `camt-twist-parser-v0.1.0`, notes from the pack's changelog.

## Tell people

- LinkedIn post with the portal screenshot and a one-line description
- A dev.to article on one pack, for example "Flattening camt.086 bank fee statements into CSV"
- Treasury, ISO 20022 and treasury-system communities you belong to
- Show HN or r/Python once the hosted demo works

### Launch post draft

> I have started TreasuryEase: small, open source automation packs that make treasury processing easier. Pack 1 turns camt.086 and TWIST bank fee statements into clean CSV or JSON, in the browser (nothing uploaded) or from the command line.
>
> Each pack does one job, has tests and synthetic examples, and is MIT licensed. Next on the list: camt.053 and MT940 to CSV, a recon diff, and a payment file checker.
>
> It is early. If you work with bank files, I would love anonymised samples and ideas for the next pack. Link in the comments.

## First week

- [ ] Answer every issue within a few days
- [ ] Turn each anonymised sample that exposes a bug into a test
- [ ] Label three issues "good first issue": a new sample layout, a docs fix, a small CLI option
- [ ] Pin an issue titled "Send us anonymised examples" that explains how to anonymise a file
