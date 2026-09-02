# UKE Menü für GitHub Pages

Die Webseite liest `data/speiseplan.json`, zeigt automatisch den aktuellen Tag
und kopiert einen an die Portionsgröße angepassten Text für YAZIO.

## Einmalige Einrichtung

1. Lade den Inhalt dieses Pakets in die oberste Ebene des Repositorys hoch.
   Die vorhandene Datei `uke_speiseplan.py` kannst du durch die Version aus
   diesem Paket ersetzen.
2. Öffne auf GitHub **Settings → Pages**.
3. Wähle unter **Build and deployment → Source** den Eintrag **GitHub Actions**.
4. Öffne den Reiter **Actions**. Starte den Workflow beim ersten Mal bei Bedarf
   über **Run workflow**. Er lädt den aktuellen Plan direkt von der UKE-Webseite.
5. Der Workflow
   „Speiseplan aktualisieren und veröffentlichen“ sollte automatisch laufen.

Nach erfolgreichem Abschluss ist die Seite normalerweise unter dieser Adresse
erreichbar:

`https://bizarrej.github.io/uke-menu-website/`

## Automatische Aktualisierung

GitHub prüft die offizielle UKE-Seite montags bis freitags morgens automatisch.
Das Skript sucht gezielt den Plan der aktuellen ISO-Kalenderwoche, lädt die PDF,
erzeugt die JSON-Datei und veröffentlicht die Webseite. Du musst keine PDF mehr
hochladen. Über **Actions → Speiseplan aktualisieren und veröffentlichen → Run
workflow** kannst du die Prüfung jederzeit manuell auslösen.

## Lokal testen

```bash
python -m pip install -r requirements.txt
python download_latest_pdf.py -o input/speiseplan.pdf
python uke_speiseplan.py input/speiseplan.pdf -o data/speiseplan.json
python -m http.server 8000
```

Anschließend `http://localhost:8000` im Browser öffnen.

## Hinweis

Das Repository und die veröffentlichte Webseite sind bei einem öffentlichen
Repository ebenfalls öffentlich. Der Workflow veröffentlicht nur die erzeugten
Menüdaten, nicht die heruntergeladene PDF.
