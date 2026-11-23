import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from camt_twist_parser import ParseError, build_table, parse_xml, to_csv, to_json  # noqa: E402
from camt_twist_parser.cli import main  # noqa: E402

SAMPLES = ROOT / "samples"
CAMT = SAMPLES / "minimal-camt086.xml"
TWIST = SAMPLES / "minimal-twist.xml"
REAL_CAMT = SAMPLES / "example-camt086.xml"
REAL_TWIST = SAMPLES / "example-twist.xml"
EXPECTED = SAMPLES / "expected"


def read(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


class DetectionTests(unittest.TestCase):
    def test_camt086_is_detected_from_namespace(self):
        f = parse_xml(CAMT)
        self.assertEqual(f.fmt.kind, "camt")
        self.assertEqual(f.fmt.tag, "camt.086.001.03")

    def test_twist_is_detected(self):
        self.assertEqual(parse_xml(TWIST).fmt.kind, "twist")

    def test_unknown_xml_is_generic(self):
        f = parse_xml("<a><b>1</b></a>")
        self.assertEqual(f.fmt.kind, "xml")

    def test_invalid_xml_raises(self):
        with self.assertRaises(ParseError):
            parse_xml("<a><b></a>")


class TableTests(unittest.TestCase):
    def test_camt_rows_are_services(self):
        t = build_table([parse_xml(CAMT)])
        self.assertEqual(len(t.rows), 5)
        self.assertEqual(t.files[0].row_stat.name, "Svc")

    def test_twist_rows_are_services(self):
        t = build_table([parse_xml(TWIST)])
        self.assertEqual(len(t.rows), 4)
        self.assertEqual(t.files[0].row_stat.name, "Service")

    def test_context_fields_repeat_on_every_row(self):
        t = build_table([parse_xml(CAMT)])
        by_label = {t.labels[c]: c for c in t.columns}
        stmt = by_label["StmtId"]
        self.assertEqual([r[stmt] for r in t.rows].count("STM-GBP-1001"), 3)
        self.assertEqual([r[stmt] for r in t.rows].count("STM-EUR-2001"), 2)

    def test_no_context_drops_header_fields(self):
        t = build_table([parse_xml(CAMT)], context=False)
        self.assertNotIn("RptId", t.labels.values())

    def test_row_element_override(self):
        t = build_table([parse_xml(CAMT)], row_element="Stmt")
        self.assertEqual(len(t.rows), 2)

    def test_repeated_elements_are_indexed_consistently(self):
        labels = set(build_table([parse_xml(CAMT)]).labels.values())
        self.assertIn("Tax[1].Amt", labels)
        self.assertIn("Tax[2].Amt", labels)
        self.assertNotIn("Tax.Amt", labels)

    def test_totals_by_currency(self):
        t = build_table([parse_xml(CAMT)])
        key = next(k for k in t.totals if t.labels[k] == "Chrg.Amt")
        # DBIT charges count as negative, CRDT as positive.
        self.assertEqual(str(t.totals[key]["GBP"][0]), "-755.83")
        self.assertEqual(str(t.totals[key]["EUR"][0]), "-137.00")

    def test_signed_amounts(self):
        t = build_table([parse_xml(CAMT)], signed=True)
        col = next(c for c in t.columns if c.endswith("Chrg/Amt~signed"))
        self.assertEqual([r[col] for r in t.rows][:3], ["-600.00", "-198.00", "42.17"])

    def test_two_files_share_one_table(self):
        t = build_table([parse_xml(CAMT), parse_xml(TWIST)])
        self.assertEqual(len(t.rows), 9)


class OutputTests(unittest.TestCase):
    def test_csv_matches_golden_files(self):
        self.assertEqual(to_csv(build_table([parse_xml(CAMT)])), read(EXPECTED / "minimal-camt086.csv"))
        self.assertEqual(to_csv(build_table([parse_xml(TWIST)])), read(EXPECTED / "minimal-twist.csv"))

    def test_json_matches_golden_file(self):
        out = to_json(build_table([parse_xml(CAMT)], signed=True))
        self.assertEqual(out, read(EXPECTED / "minimal-camt086.json"))

    def test_json_amounts_are_numbers_and_gaps_are_null(self):
        data = json.loads(to_json(build_table([parse_xml(CAMT)])))
        self.assertEqual(data[0]["Chrg.Amt"], 600)
        self.assertIsNone(data[0]["Tax[2].Amt"])

    def test_csv_quotes_values_with_delimiters(self):
        xml = "<r><Svc><Desc>a, b</Desc><Amt Ccy='GBP'>1.00</Amt></Svc><Svc><Desc>c</Desc><Amt Ccy='GBP'>2.00</Amt></Svc></r>"
        out = to_csv(build_table([parse_xml(xml)], source_column=False, context=False))
        self.assertIn('"a, b"', out)

    def test_decimal_comma(self):
        out = to_csv(build_table([parse_xml(CAMT)]), delimiter=";", decimal=",")
        self.assertIn(";600,00;", out)


class RealisticLayoutTests(unittest.TestCase):
    """Synthetic files that follow the element structure of real bank output."""

    def test_service_lines_win_over_compensation_lines(self):
        f = parse_xml(REAL_CAMT)
        t = build_table([f])
        self.assertEqual(f.row_stat.name, "Svc")
        self.assertEqual(len(t.rows), 4)

    def test_twist_rows_are_service_elements(self):
        f = parse_xml(REAL_TWIST)
        self.assertEqual(f.fmt.kind, "twist")
        build_table([f])
        self.assertEqual(f.row_stat.name, "service")

    def test_postal_addresses_are_skipped_unless_requested(self):
        without = build_table([parse_xml(REAL_CAMT)]).labels.values()
        with_ = build_table([parse_xml(REAL_CAMT)], include_addresses=True).labels.values()
        self.assertFalse(any("AdrLine" in label for label in without))
        self.assertTrue(any("AdrLine" in label for label in with_))

    def test_totals_apply_the_sign_flag(self):
        t = build_table([parse_xml(REAL_CAMT)])
        key = next(k for k in t.totals if t.labels[k] == "SvcChrgHstAmt.Amt")
        self.assertEqual(str(t.totals[key]["GBP"][0]), "1233.20")  # 1353.20 charges less a 120.00 rebate

    def test_statement_level_amounts_are_not_summed_per_row(self):
        t = build_table([parse_xml(REAL_CAMT)])
        self.assertFalse(any("TaxRgn" in k for k in t.totals))

    def test_unit_prices_and_identifiers_are_not_totalled(self):
        for path in (REAL_CAMT, REAL_TWIST):
            t = build_table([parse_xml(path)])
            labels = {t.labels[k] for k in t.totals}
            self.assertFalse({l for l in labels if "UnitPric" in l or "unitPrice" in l})
            self.assertNotIn("taxIdentifierNumber", labels)

    def test_currency_is_found_as_attribute_and_as_sibling_field(self):
        camt = build_table([parse_xml(REAL_CAMT)])
        twist = build_table([parse_xml(REAL_TWIST)])
        for t in (camt, twist):
            self.assertTrue(t.totals)
            for by_ccy in t.totals.values():
                self.assertEqual(set(by_ccy), {"GBP"})

    def test_signed_columns_follow_the_sgn_flag(self):
        t = build_table([parse_xml(REAL_CAMT)], signed=True)
        col = next(c for c in t.columns if c.endswith("SvcChrgHstAmt/Amt~signed"))
        self.assertEqual([r[col] for r in t.rows], ["144.20", "1104.00", "45.00", "-60.00"])

    def test_amounts_without_a_leading_zero_are_still_amounts(self):
        xml = ("<r><Svc><Id>a</Id><Amt Ccy='GBP'>.50</Amt></Svc>"
               "<Svc><Id>b</Id><Amt Ccy='GBP'>12.25</Amt></Svc></r>")
        t = build_table([parse_xml(xml)], source_column=False, context=False)
        key = next(k for k in t.totals if t.labels[k] == "Amt")
        self.assertEqual(str(t.totals[key]["GBP"][0]), "12.75")

    def test_golden_files(self):
        self.assertEqual(to_csv(build_table([parse_xml(REAL_CAMT)])), read(EXPECTED / "example-camt086.csv"))
        self.assertEqual(to_csv(build_table([parse_xml(REAL_TWIST)])), read(EXPECTED / "example-twist.csv"))
        self.assertEqual(to_json(build_table([parse_xml(REAL_CAMT)], signed=True)), read(EXPECTED / "example-camt086.json"))


class CliTests(unittest.TestCase):
    def test_cli_writes_csv_and_json(self):
        with tempfile.TemporaryDirectory() as d:
            out_csv, out_json = Path(d) / "o.csv", Path(d) / "o.json"
            self.assertEqual(main([str(CAMT), "-o", str(out_csv)]), 0)
            self.assertEqual(main([str(CAMT), "-o", str(out_json)]), 0)
            self.assertTrue(out_csv.read_text(encoding="utf-8").startswith("Source_file,"))
            self.assertEqual(len(json.loads(out_json.read_text(encoding="utf-8"))), 5)

    def test_cli_reports_bad_file(self):
        with tempfile.TemporaryDirectory() as d:
            bad = Path(d) / "bad.xml"
            bad.write_text("<a><b></a>")
            self.assertEqual(main([str(bad)]), 2)


if __name__ == "__main__":
    unittest.main()
