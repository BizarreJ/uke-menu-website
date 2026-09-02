#!/usr/bin/env python3
"""Lädt den UKE-Casino-Speiseplan der aktuellen ISO-Kalenderwoche."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


PAGE_URL = (
    "https://www.uke.de/organisationsstruktur/tochtergesellschaften/"
    "klinik-gastronomie-eppendorf/index.html"
)
PDF_PATH_PREFIX = "/dateien/servicegesellschaften/kge-klinik-gastronomie-eppendorf/"
PDF_NAME = re.compile(
    r"(?P<year>20\d{2})-kw-(?P<week>\d{1,2})(?:\.\d+)?\.pdf$", re.IGNORECASE
)
USER_AGENT = "uke-menu-website/1.0 (+https://github.com/BizarreJ/uke-menu-website)"


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        href = dict(attrs).get("href")
        if href:
            self.links.append(href)


@dataclass(frozen=True)
class Candidate:
    year: int
    week: int
    url: str


def request_bytes(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    with urlopen(request, timeout=30) as response:
        return response.read()


def find_candidates(html: str, page_url: str = PAGE_URL) -> list[Candidate]:
    parser = LinkParser()
    parser.feed(html)
    candidates: list[Candidate] = []
    seen: set[str] = set()

    for href in parser.links:
        url = urljoin(page_url, href)
        parsed = urlparse(url)
        if parsed.hostname not in {"uke.de", "www.uke.de"}:
            continue
        if not parsed.path.startswith(PDF_PATH_PREFIX):
            continue
        match = PDF_NAME.search(parsed.path)
        if not match or url in seen:
            continue
        seen.add(url)
        candidates.append(Candidate(int(match["year"]), int(match["week"]), url))
    return candidates


def choose_current(candidates: list[Candidate], today: date) -> Candidate:
    if not candidates:
        raise ValueError("Auf der UKE-Seite wurde kein passender PDF-Link gefunden.")

    iso_year, iso_week, _ = today.isocalendar()
    exact = [c for c in candidates if (c.year, c.week) == (iso_year, iso_week)]
    if exact:
        # Falls UKE mehrere Revisionen verlinkt, steht die aktuelle üblicherweise zuerst.
        return exact[0]

    previous = [c for c in candidates if (c.year, c.week) < (iso_year, iso_week)]
    if previous:
        return max(previous, key=lambda c: (c.year, c.week))
    raise ValueError(f"Kein Speiseplan für oder vor KW {iso_week}/{iso_year} gefunden.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-o", "--output", type=Path, default=Path("speiseplan.pdf"))
    parser.add_argument("--page-url", default=PAGE_URL, help=argparse.SUPPRESS)
    args = parser.parse_args()

    try:
        html = request_bytes(args.page_url).decode("utf-8", errors="replace")
        selected = choose_current(find_candidates(html, args.page_url), date.today())
        pdf = request_bytes(selected.url)
        if not pdf.startswith(b"%PDF-"):
            raise ValueError("Der UKE-Download ist keine gültige PDF-Datei.")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(pdf)
        print(f"KW {selected.week}/{selected.year}: {selected.url}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
