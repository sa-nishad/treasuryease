# How it works

The parser does not hard-code field paths. Banks use camt.086 and TWIST differently, so it works from the structure of each file.

## 1. Detect the format

| Signal | Result |
| --- | --- |
| Namespace contains `camt.NNN.NNN.NN` | ISO 20022 message (camt.086 gets a specific label) |
| Namespace or root name contains `twist`, or root name looks like bank service billing | TWIST |
| Anything else | Generic XML |

Detection only labels the file. The flattening below is the same for all of them.

## 2. Analyse paths

Every element is recorded under its path of local names (namespaces are ignored), for example `Document/BkSvcsBllgStmt/BllgStmtGrp/Stmt/Svc`. For each path the parser keeps:

- how many times it occurs
- whether it is a leaf (holds text) or a container
- whether any leaf below it looks like an amount: the name contains `Amt`, `Amount`, `Chrg`, `Fee`, `Tax`, `Total` and similar, or the element carries a currency attribute

## 3. Pick the row element

Candidates are containers that hold an amount.

1. If one of them is named `Svc` (camt.086) or `service` (TWIST), that is the row element. These are the billed service lines, and real statements also contain balance and compensation records that look similar but are not fees.
2. Otherwise the parser takes the **shallowest** path whose count is at least half of the highest count, preferring the one with more fields. This picks a service line (40 per file) over a tax line (80, nested inside it) and over a statement (1 per file).

If no element repeats, it chooses the deepest container with at least two fields. You can always override the choice with the **One CSV row per** selector, the Structure tab, or `--row-element`.

## 4. Flatten

For each row element:

1. Add the leaf fields of every ancestor (report header, statement), skipping the branches that lead to the row and any repeating siblings. This is the "repeat header and statement fields" option.
2. Add the row element's own fields. Attributes become `name@attribute` columns, so `<Amt Ccy="GBP">` gives `Amt` and `Amt@Ccy`.
3. If a child element repeats inside the row, it is indexed `[1]`, `[2]`.

After all rows are built, an element that is indexed in some rows is indexed in every row, so the columns line up.

## 5. Name the columns

Internally each column is its full path. For display, the shortest suffix of path parts that is unique is used, joined with `.`, and `@` becomes `_`. Generic last parts such as `Id`, `Cd` or `Nm` always keep their parent (`Acct.Id`). The Full path option uses the whole path.

## 6. Amounts, totals and signs

- A column is an **amount** if all its values are numeric (`12`, `12.50` and `.99` all count) and its name looks like an amount, or it has its own currency attribute. Names that end like identifiers, codes or rates (`Nb`, `Id`, `Cd`, `Rate`, `Number`) are not amounts.
- Currency for totals comes from the amount's own currency attribute (camt `<Amt Ccy="GBP">`), else a currency field next to it (TWIST `<currency>`), else the nearest `Ccy` or `Currency` field in an enclosing element.
- Totals cover only the columns inside the row element. Amounts from the header or statement are repeated on every row, so summing them would overcount.
- Unit prices and rates are not summed.
- Totals apply the sign flag when there is one next to the amount: `Sgn` = `false` or `CdtDbtInd` = `DBIT` makes the amount negative.
- With signed amounts on, an extra `<column>_signed` column is added next to each such amount.

## 7. Addresses

Postal address containers (`PstlAdr`, `postAddress`) are skipped unless you ask for them, because they add many columns that rarely matter for fee analysis.

## Two implementations

`web/index.html` and `src/camt_twist_parser/core.py` follow the same steps and produce identical output on the sample files. The unit tests compare the Python output to golden files in `samples/expected/`.
