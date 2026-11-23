# Format notes

## camt.086 (ISO 20022 bank services billing statement)

camt.086 carries what a bank charges for its services: a report header, one or more billing statements, and the individual services with volumes, prices, charges and taxes. The parser reads it by structure, so it should cope with different versions (`camt.086.001.0x`). The sample file `samples/example-camt086.xml` follows the element structure of real bank output with invented values.

Fields commonly of interest once flattened: report ID and creation time, period, statement ID, currency, account, service code and description, volume, unit price, charge amount with debit/credit indicator, and tax lines.

## TWIST bank service billing

TWIST publishes standards for treasury workstation integration, including a bank service billing message. Banks implement it with their own variations. `samples/example-twist.xml` is synthetic: it uses the TWIST element names, but every value is invented.

## Layouts seen so far

Version 0.1 has been run against real files of these layouts (the files themselves are private):

| Layout | Notes |
| --- | --- |
| camt.086.001.01 | `BllgStmtGrp` holds sender, receiver and one or more `BllgStmt`. Each statement has account characteristics, `Compstn` (compensation) lines, `Svc` (service) lines and a `TaxRgn` summary. Amounts are `<Amt Ccy="...">` with a sibling `<Sgn>`. |
| camt.086.001.02 | Same idea with a different tax block (`MtdC`), plus `CcyXchg`. Some amounts have no leading zero (`.99`). |
| TWIST 3.1 electronic billing | Root `Twist`, with `electronicStatement/statement`. Repeating `balance`, `compensation` and `service` elements. Amounts are `<amount>` with a sibling `<currency>`. |

What this showed, and what the parser does about it:

- Balance and compensation records look like fee lines but are not, so `Svc` and `service` are preferred as the row element.
- Statement-level amounts repeat on every row, so totals only count amounts inside the row element.
- Currency is sometimes an attribute and sometimes a sibling field, so both are handled.
- A sign flag sits beside each amount (`Sgn`), so totals and the optional signed columns use it.

## Still unverified

Other banks, other versions (for example camt.086.001.03 and later) and files with several accounts or currencies per statement may differ. Anonymised examples are the best way to improve coverage. See [DEVELOPMENT.md](../DEVELOPMENT.md).

## Sending an example

1. Copy the file.
2. Replace every name, account number, IBAN, BIC, reference and amount.
3. Keep element names, nesting, attributes and the repeated structure.
4. Open the copy in the web app to confirm it still reproduces the problem.
5. Paste it into an issue.
