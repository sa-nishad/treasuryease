# Contributing to TreasuryEase

Thank you. This repository holds several independent packs, so contributions fall into three kinds.

## 1. Improve an existing pack

Open the pack's own README and `DEVELOPMENT.md` if it has one. Run its tests before you start and again before you open a pull request.

## 2. Add a new pack

1. Check [docs/ROADMAP.md](docs/ROADMAP.md) and open an issue with the "Pack idea" template so we can agree on scope first.
2. Create it: `python tools/new_pack.py my-pack "My Pack" "One sentence on what it does."`
3. Follow the [pack guide](docs/PACK_GUIDE.md): README, synthetic samples, tests, `pack.json`.
4. Run `python tools/check_packs.py` and `python tools/run_tests.py`.
5. Open a pull request using the template.

## 3. Send an anonymised sample

New real-world layouts are the best way to make a pack better. Before you attach anything:

- Replace names, account numbers, IBANs, BICs, references and amounts.
- Keep element names, nesting, attributes and the pattern of repeated elements.
- Check file names too. Bank file names often contain account numbers.
- Never attach an unmodified file, even if you think it is harmless.

If you are unsure whether a file is safe to share, it is not. Describe the structure in words instead.

## Rules for every pack

- No real client, bank or account data anywhere in the repository.
- No network calls with user data.
- No runtime dependencies unless there is a strong reason, and then say why in the README.
- Tests for anything marked available or beta.
- Output is CSV or JSON unless the pack's job needs something else.

## Pull request checklist

- [ ] `python tools/check_packs.py` reports no problems
- [ ] `python tools/run_tests.py` passes
- [ ] Samples are synthetic
- [ ] The pack's README and changelog describe the change
- [ ] If the change affects two implementations of the same logic (for example JavaScript and Python), both are updated

## Conduct

Be kind and assume good faith. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
