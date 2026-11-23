# Pack guide

A pack is a small, finished tool that does one job for people who work with treasury systems and bank files.

## Layout

```
packs/my-pack/
  pack.json        Metadata for the site and checks (required)
  README.md        What it does, quick start, how it works, limits (required)
  CHANGELOG.md     User-visible changes
  web/index.html   Browser app, single file, optional
  src/             Python package, optional
  tests/           Unit tests (required for available and beta packs)
  samples/         Synthetic input files and expected output
  docs/            Longer notes and screenshots
```

Create one with `python tools/new_pack.py my-pack "My Pack" "One sentence."`.

## pack.json

```json
{
  "id": "my-pack",
  "name": "My Pack",
  "summary": "One sentence, plain words.",
  "status": "beta",
  "version": "0.1.0",
  "tags": ["camt.053", "CSV"],
  "web": "web",
  "screenshot": "docs/screenshots/table.png",
  "cli": "my-pack",
  "docs": "README.md"
}
```

| Field | Meaning |
| --- | --- |
| `id` | Folder name. Lower case words joined by hyphens. |
| `status` | `idea`, `beta` or `available`. Beta and available need tests. |
| `web` | Folder containing `index.html`. The site publishes it at `/packs/<id>/`. |
| `screenshot` | Image shown on the site card. Use synthetic data. |

## Standards

**Private by design.** Process files locally. No telemetry, no uploads, no network calls with user data.

**Synthetic samples.** Use real element names from the public schemas and invented values. Fake IBANs should fail the mod-97 check (for example `GB00EXAM...`), and company names should be obviously fictional. The repository check scans for valid IBANs and for long numbers in file names.

**Deterministic output.** The same input gives the same output. Keep expected output files in `samples/expected/` and compare against them in tests.

**One logic, one source of truth.** If a pack has both a browser app and a Python tool, they must produce identical output. Say so in the pack's development notes and test it.

**Say what is unverified.** The README's "Status and limits" section states what the pack has been tested on and what has not been tried.

**Small interface.** A drop zone and a download button beats a settings page. Put advanced choices behind plain-language options.

**Accessible and themed.** Keyboard focus is visible, controls have labels, and the page follows light and dark mode.

## Definition of done

- [ ] README answers: what problem, what it does, how to run it, how it works, what is unverified
- [ ] `pack.json` is complete and `python tools/check_packs.py` is clean
- [ ] Tests pass on Python 3.9 and later, if the pack has Python code
- [ ] Samples and screenshots contain no real data
- [ ] Output checked against a source statement or an independent calculation
- [ ] Changelog entry written

## Versioning and releases

Each pack has its own version. Tag releases as `<pack-id>-v<version>`, for example `camt-twist-parser-v0.1.0`, and write the release notes from the pack's changelog.
