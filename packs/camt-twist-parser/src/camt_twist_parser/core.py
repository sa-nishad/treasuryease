"""Core parsing logic for camt.086 and TWIST bank service billing XML.

The algorithm mirrors the browser app in ``web/index.html`` so both produce the
same columns and rows. It uses only the Python standard library.

Overview
--------
1. Parse the XML and detect the format from the namespace / root element.
2. Walk the tree and collect statistics per element path.
3. Pick the repeating "record" element (for example ``Svc``) that carries amounts.
4. Flatten each record into one row: the record's own fields, plus the fields of
   its ancestors (header, statement) so every row is self-contained.
5. Build readable column names, add optional signed amounts, compute totals.
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

AMT_RE = re.compile(r"amt|amount|chrg|charge|fee|tax|vat|ttl|total|pric|cost", re.I)
# Names that look like amounts but are identifiers, codes or rates.
NOT_AMT_RE = re.compile(
    r"(number|identifier|id|nb|code|cd|region|rgn|designation|method|mtd|reason|rsn|rate|ref)$", re.I
)
# Accepts 12, 12.50, .99 (some banks omit the leading zero) and 12.
NUM_RE = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)")
CCY_RE = re.compile(r"(ccy|currency|currencycode)", re.I)
# Names of currency fields, for example Ccy, HstCcyCd, currency, settlementCurrencyCode.
CCY_NAME_RE = re.compile(r"(?:^|[a-z])(?:ccy|currency)(?:cd|code)?$", re.I)
# Element names that hold one billed service. Preferred when present (camt.086, TWIST).
SERVICE_ROWS = {"svc", "service"}
# Postal address containers, skipped unless include_addresses is set.
ADDRESS_NAMES = {"PstlAdr", "postAddress"}
# Fields that flag the sign of an amount: (field name, value that means negative).
SIGN_FIELDS = (("CdtDbtInd", "DBIT"), ("Sgn", "false"))
GENERIC_RE = re.compile(r"(Id|Cd|Nm|Tp|Othr|Prtry|Ref|Dt)(_.*)?")


class ParseError(Exception):
    """Raised when a file cannot be read as XML."""


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #


@dataclass
class FormatInfo:
    kind: str  # "camt", "twist" or "xml"
    tag: str  # for example "camt.086.001.03", "TWIST", "XML"
    label: str


@dataclass
class PathStat:
    path: str
    name: str
    depth: int
    count: int = 0
    is_leaf: bool = True
    sample: str = ""
    children: Dict[str, None] = field(default_factory=dict)
    amt_leaf: bool = False
    leaf_count: int = 0
    amt: bool = False


@dataclass
class ParsedFile:
    name: str
    root: ET.Element
    fmt: FormatInfo
    stats: Dict[str, PathStat]
    parents: Dict[ET.Element, Optional[ET.Element]]
    row_stat: Optional[PathStat] = None
    row_count: int = 0


@dataclass
class Table:
    columns: List[str]
    rows: List[Dict[str, str]]
    labels: Dict[str, str]
    amount_columns: List[str]
    totals: Dict[str, Dict[str, Tuple[Decimal, int]]]
    warnings: List[str]
    files: List[ParsedFile]


# --------------------------------------------------------------------------- #
# Reading and detecting
# --------------------------------------------------------------------------- #


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def namespace(tag: str) -> str:
    return tag[1:].split("}", 1)[0] if tag.startswith("{") else ""


def detect(root: ET.Element) -> FormatInfo:
    ns = namespace(root.tag)
    m = re.search(r"camt\.(\d{3})\.(\d{3})\.(\d{2})", ns, re.I)
    if m:
        msg = m.group(1)
        label = (
            "ISO 20022 camt.086 bank services billing"
            if msg == "086"
            else f"ISO 20022 camt.{msg}"
        )
        return FormatInfo("camt", f"camt.{msg}.{m.group(2)}.{m.group(3)}", label)
    name = local(root.tag)
    if re.search(r"twist", ns, re.I) or re.search(r"twist", name, re.I) or re.search(
        r"bank.?serv|bsb|billing", name, re.I
    ):
        return FormatInfo("twist", "TWIST", "TWIST bank service billing")
    return FormatInfo("xml", "XML", "Generic XML")


def _analyse(root: ET.Element) -> Dict[str, PathStat]:
    stats: Dict[str, PathStat] = {}

    def walk(el: ET.Element, path: str, depth: int) -> None:
        s = stats.get(path)
        if s is None:
            s = PathStat(path=path, name=local(el.tag), depth=depth)
            stats[path] = s
        s.count += 1
        kids = list(el)
        if kids:
            s.is_leaf = False
        else:
            if not s.sample:
                s.sample = (el.text or "").strip()[:60]
            has_ccy = any(CCY_RE.fullmatch(local(a)) for a in el.attrib)
            if (AMT_RE.search(s.name) and not NOT_AMT_RE.search(s.name)) or has_ccy:
                s.amt_leaf = True
        for k in kids:
            p = path + "/" + local(k.tag)
            s.children[p] = None
            walk(k, p, depth + 1)

    walk(root, local(root.tag), 0)

    memo: Dict[str, Tuple[int, bool]] = {}

    def info(p: str) -> Tuple[int, bool]:
        if p in memo:
            return memo[p]
        s = stats[p]
        if s.is_leaf:
            r = (1, s.amt_leaf)
        else:
            leaves, amt = 0, False
            for c in s.children:
                a, b = info(c)
                leaves += a
                amt = amt or b
            r = (leaves, amt)
        memo[p] = r
        return r

    for s in stats.values():
        s.leaf_count, s.amt = info(s.path)
    return stats


def parse_xml(source: "str | bytes | Path", name: Optional[str] = None) -> ParsedFile:
    """Parse XML from a path, bytes or text and analyse its structure."""
    if isinstance(source, Path):
        name = name or source.name
        data: "str | bytes" = source.read_bytes()
    else:
        data = source
    try:
        if isinstance(data, str):
            data = data.lstrip("﻿").encode("utf-8")
            root = ET.fromstring(data)
        else:
            root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ParseError(str(exc)) from exc
    parents: Dict[ET.Element, Optional[ET.Element]] = {root: None}
    for el in root.iter():
        for k in el:
            parents[k] = el
    return ParsedFile(
        name=name or "input.xml",
        root=root,
        fmt=detect(root),
        stats=_analyse(root),
        parents=parents,
    )


# --------------------------------------------------------------------------- #
# Row selection and flattening
# --------------------------------------------------------------------------- #


def pick_row(stats: Dict[str, PathStat], name: str = "auto") -> PathStat:
    """Choose which repeating element becomes one output row."""
    allv = list(stats.values())
    if name != "auto":
        m = sorted(
            (s for s in allv if not s.is_leaf and s.name == name),
            key=lambda s: (-s.count, s.depth),
        )
        if m:
            return m[0]
    pool = [s for s in allv if not s.is_leaf and s.amt and s.depth > 0]
    services = [s for s in pool if s.name.lower() in SERVICE_ROWS]
    if services:
        return sorted(services, key=lambda s: (s.depth, -s.count))[0]
    if not pool:
        pool = [s for s in allv if not s.is_leaf and s.count > 1]
    if not pool:
        return allv[0]
    top = max(s.count for s in pool)
    if top == 1:
        ok = [s for s in pool if s.leaf_count >= 2]
        return sorted(ok or pool, key=lambda s: -s.depth)[0]
    near = [s for s in pool if s.count >= top / 2]
    return sorted(near, key=lambda s: (s.depth, -s.leaf_count, -s.count))[0]


def row_element_options(files: Iterable[ParsedFile]) -> List[Tuple[str, int]]:
    """Element names that could serve as the row element, with their counts."""
    names: Dict[str, int] = {}
    for f in files:
        for s in f.stats.values():
            if not s.is_leaf and s.depth > 0 and (s.count > 1 or s.amt):
                names[s.name] = names.get(s.name, 0) + s.count
    multi = {k: v for k, v in names.items() if v > 1}
    pick = multi or names
    return sorted(pick.items(), key=lambda kv: -kv[1])[:12]


def _find_all(root: ET.Element, parts: List[str]) -> List[ET.Element]:
    cur = [root]
    for part in parts[1:]:
        cur = [k for e in cur for k in e if local(k.tag) == part]
    return cur


def _attrs_into(row: Dict[str, str], key: str, el: ET.Element) -> None:
    for a, v in el.attrib.items():
        row[f"{key}@{local(a)}"] = v


SkipFn = Callable[[ET.Element, str, int], bool]


def _collect(
    el: ET.Element,
    prefix: str,
    row: Dict[str, str],
    skip: Optional[SkipFn],
    path: str,
) -> None:
    kids = list(el)
    if not kids:
        return
    counts: Dict[str, int] = {}
    for k in kids:
        counts[local(k.tag)] = counts.get(local(k.tag), 0) + 1
    seen: Dict[str, int] = {}
    for k in kids:
        nm = local(k.tag)
        cp = f"{path}/{nm}"
        if skip and skip(k, cp, counts[nm]):
            continue
        seg = nm
        if counts[nm] > 1:
            seen[nm] = seen.get(nm, 0) + 1
            seg = f"{nm}[{seen[nm]}]"
        key = prefix + seg
        if len(k):
            _attrs_into(row, key, k)
            _collect(k, key + "/", row, skip, cp)
        else:
            row[key] = (k.text or "").strip()
            _attrs_into(row, key, k)


def _normalise_indexes(rows: List[Dict[str, str]]) -> None:
    """If an element repeats in some rows, index it as [1] in the others too."""
    prefixes: Dict[str, None] = {}
    for r in rows:
        for k in r:
            for m in re.finditer(r"\[1\]", k):
                prefixes[k[: m.start()]] = None
    if not prefixes:
        return
    ordered = sorted(prefixes, key=len)
    for i, r in enumerate(rows):
        out: Dict[str, str] = {}
        changed = False
        for k, v in r.items():
            nk = k
            for p in ordered:
                if nk == p or nk.startswith(p + "/") or nk.startswith(p + "@"):
                    nk = p + "[1]" + nk[len(p):]
                    changed = True
                    break
            out[nk] = v
        if changed:
            rows[i] = out


def _has_own_ccy(key: str, cols: set) -> bool:
    return any(
        c.startswith(key + "@") and CCY_RE.fullmatch(c[len(key) + 1:]) for c in cols
    )


def _ccy_for(key: str, cols: List[str]) -> Optional[str]:
    """Find the column that holds the currency for an amount column.

    Order: a currency attribute on the amount itself (``<Amt Ccy="GBP">``), a
    currency field next to the amount (TWIST ``currency``), then the nearest
    currency field in an enclosing element.
    """
    base = key.split("~", 1)[0]
    for c in cols:
        if c.startswith(base + "@") and CCY_RE.fullmatch(c[len(base) + 1:]):
            return c
    parts = base.split("/")[:-1]
    for i in range(len(parts), -1, -1):
        pre = "/".join(parts[:i])
        found = [
            c
            for c in cols
            if "@" not in c
            and c.rsplit("/", 1)[0] == pre
            and c != base
            and CCY_NAME_RE.search(c.rsplit("/", 1)[-1])
        ]
        if found:
            return sorted(found, key=len)[0]
    return None


def _make_labels(cols: List[str], naming: str) -> Dict[str, str]:
    def segs(k: str) -> List[str]:
        return [re.sub(r"[@~]", "_", s) for s in k.split("/")]

    def label_for(k: str) -> str:
        if k == "#file":
            return "Source_file"
        if "~" in k:
            i = k.index("~")
            return label_for(k[:i]) + "_" + k[i + 1:]
        sg = segs(k)
        if naming == "full":
            return ".".join(sg)
        generic = bool(GENERIC_RE.fullmatch(sg[-1]))
        for n in range(2 if generic else 1, len(sg) + 1):
            cand = ".".join(sg[-n:])
            clash = any(
                o != k and o != "#file" and ".".join(segs(o)[-n:]) == cand for o in cols
            )
            if not clash:
                return cand
        return ".".join(sg)

    used: set = set()
    out: Dict[str, str] = {}
    for k in cols:
        label = label_for(k)
        base, i = label, 2
        while label in used:
            label = f"{base}_{i}"
            i += 1
        used.add(label)
        out[k] = label
    return out


def build_table(
    files: List[ParsedFile],
    row_element: str = "auto",
    context: bool = True,
    source_column: bool = True,
    signed: bool = False,
    naming: str = "short",
    include_addresses: bool = False,
) -> Table:
    """Flatten parsed files into a single table."""
    rows: List[Dict[str, str]] = []
    warnings: List[str] = []
    row_bases: List[str] = []
    no_address: Optional[SkipFn] = (
        None if include_addresses else (lambda k, cp, n: local(k.tag) in ADDRESS_NAMES)
    )

    for f in files:
        st = pick_row(f.stats, row_element)
        f.row_stat = st
        parts = st.path.split("/")
        els = _find_all(f.root, parts)
        chain = {"/".join(parts[: i + 1]) for i in range(len(parts))}
        base = "/".join(parts)
        row_bases.append(base)
        cache: Dict[ET.Element, Dict[str, str]] = {}
        f.row_count = len(els)
        if not els:
            warnings.append(f"{f.name}: no records found.")
        for el in els:
            row: Dict[str, str] = {}
            if source_column:
                row["#file"] = f.name
            if context:
                anc: List[ET.Element] = []
                p = f.parents.get(el)
                while p is not None:
                    anc.insert(0, p)
                    p = f.parents.get(p)
                for i, a in enumerate(anc):
                    c = cache.get(a)
                    if c is None:
                        c = {}
                        ap = "/".join(parts[: i + 1])
                        _attrs_into(c, ap, a)
                        _collect(
                            a,
                            ap + "/",
                            c,
                            lambda k, cp, n: cp in chain
                            or (len(k) > 0 and n > 1)
                            or (no_address is not None and no_address(k, cp, n)),
                            ap,
                        )
                        cache[a] = c
                    row.update(c)
            _attrs_into(row, base, el)
            _collect(el, base + "/", row, no_address, base)
            rows.append(row)
        if st.depth == 0 and st.count == 1:
            warnings.append(
                f"{f.name}: no repeating records found, so the whole file is one row. "
                "Use --row-element to choose one."
            )

    _normalise_indexes(rows)
    cols: List[str] = []
    colset: set = set()
    for r in rows:
        for k in r:
            if k not in colset:
                colset.add(k)
                cols.append(k)

    numeric: set = set()
    amount: set = set()
    for k in cols:
        if k == "#file":
            continue
        any_v, ok = False, True
        for r in rows:
            v = r.get(k, "")
            if v == "":
                continue
            any_v = True
            if not NUM_RE.fullmatch(v):
                ok = False
                break
        if any_v and ok:
            numeric.add(k)
            last = k.split("/")[-1]
            if (AMT_RE.search(last) and not NOT_AMT_RE.search(last)) or _has_own_ccy(k, colset):
                amount.add(k)

    if signed:
        out_cols: List[str] = []
        for k in cols:
            out_cols.append(k)
            if k not in amount:
                continue
            parent = k[: k.rfind("/")]
            flag = next(
                ((f"{parent}/{n}", neg) for n, neg in SIGN_FIELDS if f"{parent}/{n}" in colset),
                None,
            )
            if flag is None:
                continue
            ik, negative = flag
            sk = k + "~signed"
            for r in rows:
                v, ind = r.get(k, ""), r.get(ik, "")
                if v == "" or not ind:
                    continue
                s = re.sub(r"^[+-]", "", v)
                r[sk] = "-" + s if ind.lower() == negative.lower() else s
            colset.add(sk)
            out_cols.append(sk)
            numeric.add(sk)
            amount.add(sk)
        cols = out_cols

    totals: Dict[str, Dict[str, Tuple[Decimal, int]]] = {}
    for k in cols:
        if k not in amount or "~" in k:
            continue
        if re.search(r"unit|rate", "/".join(k.split("/")[-2:]), re.I):
            continue
        # Amounts from header or statement fields repeat on every row; summing them would overcount.
        if not any(k.startswith(b + "/") for b in row_bases):
            continue
        parent = k[: k.rfind("/")]
        flag = next(
            ((f"{parent}/{n}", neg) for n, neg in SIGN_FIELDS if f"{parent}/{n}" in colset),
            None,
        )
        ck = _ccy_for(k, cols)
        m: Dict[str, Tuple[Decimal, int]] = {}
        for r in rows:
            v = r.get(k, "")
            if v == "":
                continue
            amount_value = Decimal(v)
            if flag and r.get(flag[0], "").lower() == flag[1].lower():
                amount_value = -amount_value
            cur = (ck and r.get(ck)) or "n/a"
            tot, n = m.get(cur, (Decimal(0), 0))
            m[cur] = (tot + amount_value, n + 1)
        totals[k] = m

    return Table(
        columns=cols,
        rows=rows,
        labels=_make_labels(cols, naming),
        amount_columns=[c for c in cols if c in amount],
        totals=totals,
        warnings=warnings,
        files=files,
    )


# --------------------------------------------------------------------------- #
# Output
# --------------------------------------------------------------------------- #


def _quote(v: str, delim: str, quote_all: bool) -> str:
    need = (
        quote_all
        or delim in v
        or any(c in v for c in '"\r\n')
        or v != v.strip()
    )
    return '"' + v.replace('"', '""') + '"' if need else v


def to_csv(
    table: Table,
    delimiter: str = ",",
    quote_all: bool = False,
    eol: str = "\r\n",
    header: bool = True,
    decimal: str = ".",
    hidden: Iterable[str] = (),
) -> str:
    """Render the table as CSV text."""
    hide = set(hidden)
    vis = [c for c in table.columns if c not in hide]
    amount = set(table.amount_columns)
    lines: List[str] = []
    if header:
        lines.append(delimiter.join(_quote(table.labels[c], delimiter, quote_all) for c in vis))
    for r in table.rows:
        cells = []
        for c in vis:
            v = r.get(c, "")
            if decimal != "." and v != "" and c in amount:
                v = v.replace(".", decimal, 1)
            cells.append(_quote(v, delimiter, quote_all))
        lines.append(delimiter.join(cells))
    return eol.join(lines) + eol if lines else ""


def to_json(
    table: Table,
    numbers: bool = True,
    indent: Optional[int] = 2,
    hidden: Iterable[str] = (),
) -> str:
    """Render the table as a JSON array of objects."""
    hide = set(hidden)
    vis = [c for c in table.columns if c not in hide]
    amount = set(table.amount_columns)
    out = []
    for r in table.rows:
        obj = {}
        for c in vis:
            v: object = r.get(c, "")
            if v == "":
                v = None
            elif numbers and c in amount:
                f = float(v)  # type: ignore[arg-type]
                v = int(f) if f.is_integer() else f
            obj[table.labels[c]] = v
        out.append(obj)
    return json.dumps(out, indent=indent, ensure_ascii=False) + "\n"


def summary_lines(table: Table) -> List[str]:
    """Human-readable totals by column and currency."""
    lines: List[str] = []
    for f in table.files:
        el = f.row_stat.path.split("/")[-1] if f.row_stat else "?"
        lines.append(f"{f.name}: {f.fmt.tag}, {f.row_count} rows (one per <{el}>)")
    for k, by_ccy in table.totals.items():
        for ccy, (total, n) in by_ccy.items():
            lines.append(f"  {table.labels[k]:<24} {ccy:<4} {total:>14}  ({n} rows)")
    lines.extend(f"warning: {w}" for w in table.warnings)
    return lines
