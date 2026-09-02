#!/usr/bin/env python3
"""UKE-Speiseplan aus einer PDF in JSON oder YAZIO-Text umwandeln.

Abhaengigkeit:
    python -m pip install pdfplumber

Beispiele:
    python uke_speiseplan.py 2026-kw-36.3.pdf
    python uke_speiseplan.py 2026-kw-36.3.pdf -o speiseplan.json
    python uke_speiseplan.py 2026-kw-36.3.pdf --date 2026-09-02 --text
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

import pdfplumber
from PIL import Image


WEEKDAYS = ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag")
MENU_ROWS = (
    ("Menü 1", 108, 198),
    ("Menü 2", 198, 280),
    ("Menü 3", 280, 370),
    ("Wok Grill", 370, 460),
)
MONTHS = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4,
    "mai": 5, "juni": 6, "juli": 7, "august": 8, "september": 9,
    "oktober": 10, "november": 11, "dezember": 12,
}

# Perceptual hashes der im UKE-Plan verwendeten Ernährungssymbole. Die Namen
# /Image1, /Image2 usw. sind nicht stabil oder aussagekräftig, der Bildinhalt
# dagegen schon. Mehrere Hashes decken leicht anders skalierte Varianten ab.
ICON_HASHES = {
    "vegan": (
        "010e047c21f00fc27e36f0b6c5d6869ab4acb4c6b4b0b180c902f010c0808200",
        "010e087c21f20fc23e26f0b6c5d6869ab4acb486b4b0b1808902f010c0408200",
        "011e087c23e20f027ca6f0b6c5d6869aa5aaa484b4b0b1808904b010c0808200",
        "010e087c21f20fc27e36f0b685d6869eb4acb4c6b4b0b980c902f010c0808200",
        "011e087c43e20f827ca6e0b685d6869aa5aca486b4b0b9808904b010c0808400",
    ),
    "vegetarisch": (
        "3c41f198ca9ca47e493111e9a782ce24f1b87e010f00a254d6d4d25400008240",
        "3c41f190ca9ca47e493011e8a7828e24f1b87e010f00a25cd6dcd25c00008240",
        "3c41f190ca9ca47e493111e9a782ce64f1b87e010f00a2dcd6d8d25c00008000",
        "3e01f1b0ca9ca47e493111e9a7828e24f1b87e010f00a2dcd6d8d25c00008100",
    ),
    "rind": (
        "d070e0028c0993e8e804f4087408b4a8ba4859b13cb50c3c2d582958595c5904",
        "d050e0028c0993e8e004f4087408b4a8ba4859b13cb52c3c2d5c2958595c5904",
        "d070c002ac0993e8e804f4087408b4a8bb4859b12cb52c382d582958595c5904",
        "2c020f8043f65017108b100788070a1704b72657034a1302028716a706a32683",
    ),
    "schwein": (
        "30046e80d060d01e8000a004a002c002d007d0d8d520d6e190c492c4d2d4dad0",
    ),
    "geflügel": (
        "002e005c20fa98b4806861e89994a264d004e8087631b8c25f0427101b000780",
        "002e805e20fa98b48068e1e89998a264d004e8087631b8c25f0427101b000780",
        "002e805e20fa98b4806861e89990a264d004e8087631b8c25f0427101b000780",
    ),
    "fisch": (
        "00a040c4a072c87c608f73134c05200248023605710bc0a7245e405802c40090",
        "80010001031d3b014b81077c8e02c902d304cc388fc101834508410303ff7f80",
    ),
}

TEXT_PROTEINS = {
    "fisch": ("fisch", "lachs", "thunfisch", "matjes", "kabeljau", "seelachs"),
    "geflügel": ("chicken", "hähn", "huhn", "pute", "ente"),
    "rind": ("rind", "kalb", "vitello"),
    "schwein": ("schwein", "speck", "schinken"),
}
VEGETARIAN_WORDS = (
    "käse", "mozzarella", "hirtenkäse", "grana padano", "sauerrahm",
    "spinatknödel", "ei ",
)


def parse_start_date(title: str) -> date:
    """Liest das erste Datum aus z. B. 'vom 31. August bis ... 2026'."""
    match = re.search(
        r"vom\s+(\d{1,2})\.\s+([A-Za-zÄÖÜäöü]+).*?(\d{4})", title, re.I
    )
    if not match:
        raise ValueError("Zeitraum im PDF-Titel nicht erkannt.")
    day, month_name, year = match.groups()
    month = MONTHS.get(month_name.casefold())
    if month is None:
        raise ValueError(f"Unbekannter Monatsname: {month_name}")
    return date(int(year), month, int(day))


def clean_cell(text: str) -> dict[str, object]:
    """Trennt Gericht, Preise, Allergene und kcal einer Tabellenzelle."""
    text = re.sub(r"\s+", " ", text).strip()
    kcal_match = re.search(r"Nährwert:\s*ca\.\s*(\d+)\s*Kcal", text, re.I)
    price_matches = list(re.finditer(r"(\d+,\d{2})\s*€", text))
    if not kcal_match or len(price_matches) < 2:
        raise ValueError(f"Zelle konnte nicht vollständig gelesen werden: {text!r}")

    food = text[: price_matches[0].start()].strip(" €/")
    # Einzelne, am Spaltenrand eingefangene Eurozeichen entfernen.
    food = re.sub(r"^€\s*", "", food).strip()
    parts = [part.strip() for part in food.split("/") if part.strip()]
    title = parts[0] if parts else food

    metadata = text[price_matches[1].end() : kcal_match.start()]
    allergen_match = re.search(r"enthält:?\s*([A-Z](?:\s*,\s*[A-Z])*)", metadata, re.I)
    allergens = []
    if allergen_match:
        allergens = [x.strip().upper() for x in allergen_match.group(1).split(",")]

    return {
        "gericht": title,
        "beschreibung": food,
        "kcal": int(kcal_match.group(1)),
        "preis_intern_eur": float(price_matches[0].group(1).replace(",", ".")),
        "preis_extern_eur": float(price_matches[1].group(1).replace(",", ".")),
        "allergene": allergens,
        "yazio_text": f"{food}. Portion laut UKE-Casino ca. {kcal_match.group(1)} kcal.",
    }


def difference_hash(image: Image.Image, size: int = 16) -> int:
    """Robuster 256-Bit-Bildhash, unabhängig von der Originalauflösung."""
    gray = image.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    # get_flattened_data ist der Pillow-Nachfolger von getdata; der Fallback
    # hält das Skript mit älteren Pillow-Versionen kompatibel.
    getter = getattr(gray, "get_flattened_data", gray.getdata)
    pixels = list(getter())
    result = 0
    for y in range(size):
        row = pixels[y * (size + 1) : (y + 1) * (size + 1)]
        for x in range(size):
            result = (result << 1) | (row[x] > row[x + 1])
    return result


def image_from_pdf_object(image: dict[str, object]) -> Image.Image | None:
    """Dekodiert die hier verwendeten RGB-Bildobjekte aus pdfplumber."""
    try:
        width, height = image["srcsize"]
        raw = image["stream"].get_data()
        if len(raw) == width * height * 3:
            return Image.frombytes("RGB", (width, height), raw)
    except (KeyError, OSError, TypeError, ValueError):
        pass
    return None


def recognize_icons(images: list[dict[str, object]], max_distance: int = 18) -> set[str]:
    """Erkennt Ernährungslogos per kleinstem Hamming-Abstand zum Referenzhash."""
    found: set[str] = set()
    references = {
        label: [int(value, 16) for value in hashes]
        for label, hashes in ICON_HASHES.items()
    }
    for pdf_image in images:
        decoded = image_from_pdf_object(pdf_image)
        if decoded is None:
            continue
        candidate = difference_hash(decoded)
        best_label = None
        best_distance = 257
        for label, hashes in references.items():
            distance = min((candidate ^ reference).bit_count() for reference in hashes)
            if distance < best_distance:
                best_label, best_distance = label, distance
        if best_label is not None and best_distance <= max_distance:
            found.add(best_label)
    return found


def classify_food(description: str, icons: set[str]) -> dict[str, object]:
    text = description.casefold()
    sources: set[str] = set()
    proteins = {label for label in ("rind", "schwein", "geflügel", "fisch") if label in icons}
    if icons:
        sources.add("symbol")

    text_proteins = {
        label for label, words in TEXT_PROTEINS.items() if any(word in text for word in words)
    }
    if text_proteins:
        proteins.update(text_proteins)
        sources.add("text")

    # Eine explizite Vegan-Kennzeichnung hat Vorrang vor Begriffen wie
    # "Gyros" oder "Currywurst", die auch vegane Varianten bezeichnen können.
    if "vegan" in icons or re.search(r"\bvegan\w*\b", text):
        form = "vegan"
        proteins.clear()
        if "vegan" in text:
            sources.add("text")
    elif "vegetarisch" in icons:
        form = "vegetarisch"
    elif proteins:
        form = "fleisch/fisch"
    elif any(word in text for word in VEGETARIAN_WORDS):
        form = "vegetarisch"
        sources.add("text")
    else:
        form = "unbekannt"

    labels = sorted(icons & {"vegan", "vegetarisch"})
    return {
        "ernaehrungsform": form,
        "proteintypen": sorted(proteins),
        "kennzeichnungen": labels,
        "klassifizierung_quellen": sorted(sources),
        "klassifizierung_sicher": form != "unbekannt" and bool(sources),
    }


def extract_menu(pdf_path: Path) -> dict[str, object]:
    with pdfplumber.open(pdf_path) as pdf:
        if not pdf.pages:
            raise ValueError("Die PDF enthält keine Seiten.")
        page = pdf.pages[0]
        title_area = page.crop((0, 0, page.width, 50)).extract_text() or ""
        start = parse_start_date(title_area)

        # Relative X-Grenzen machen das Skript unempfindlicher gegen Skalierung.
        x_ratios = (0.1176, 0.2934, 0.4679, 0.6414, 0.8124, 0.9858)
        scale_y = page.height / 595.32
        x_bounds = [ratio * page.width for ratio in x_ratios]
        days: dict[str, object] = {}

        for day_index, weekday in enumerate(WEEKDAYS):
            current_date = start + timedelta(days=day_index)
            menus = []
            for menu_name, top, bottom in MENU_ROWS:
                box = (
                    x_bounds[day_index], top * scale_y,
                    x_bounds[day_index + 1], bottom * scale_y,
                )
                cell_text = page.crop(box).extract_text(x_tolerance=1, y_tolerance=3)
                if not cell_text:
                    continue
                item = clean_cell(cell_text)
                cell_images = [
                    image for image in page.images
                    if box[0] <= (image["x0"] + image["x1"]) / 2 < box[2]
                    and box[1] <= (image["top"] + image["bottom"]) / 2 < box[3]
                ]
                icons = recognize_icons(cell_images)
                item.update(classify_food(str(item["beschreibung"]), icons))
                item["menü"] = menu_name
                menus.append(item)
            days[current_date.isoformat()] = {"wochentag": weekday, "gerichte": menus}

    return {
        "quelle": pdf_path.name,
        "zeitraum_von": start.isoformat(),
        "zeitraum_bis": (start + timedelta(days=4)).isoformat(),
        "tage": days,
    }


def format_day(data: dict[str, object], selected_date: str) -> str:
    days = data["tage"]
    assert isinstance(days, dict)
    day = days.get(selected_date)
    if not isinstance(day, dict):
        available = ", ".join(days)
        raise ValueError(f"Datum {selected_date} nicht im Plan. Verfügbar: {available}")
    lines = [f"{day['wochentag']}, {selected_date}", ""]
    for item in day["gerichte"]:
        lines.extend((f"{item['menü']}: {item['gericht']}", item["yazio_text"], ""))
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path, help="Pfad zur UKE-Speiseplan-PDF")
    parser.add_argument("-o", "--output", type=Path, help="Ausgabe in Datei statt stdout")
    parser.add_argument("--date", help="Nur diesen Tag ausgeben (YYYY-MM-DD)")
    parser.add_argument("--text", action="store_true", help="Kopiertext statt JSON ausgeben")
    args = parser.parse_args()

    try:
        data = extract_menu(args.pdf)
        if args.text:
            selected_date = args.date or date.today().isoformat()
            result = format_day(data, selected_date)
        else:
            if args.date:
                days = data["tage"]
                assert isinstance(days, dict)
                if args.date not in days:
                    raise ValueError(f"Datum {args.date} nicht im Plan.")
                data = {**data, "tage": {args.date: days[args.date]}}
            result = json.dumps(data, ensure_ascii=False, indent=2) + "\n"

        if args.output:
            args.output.write_text(result, encoding="utf-8")
        else:
            sys.stdout.write(result)
        return 0
    except (OSError, ValueError) as exc:
        print(f"Fehler: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
