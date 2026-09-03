# UKE Menü für GitHub Pages

Die Vue-3-Webseite liest den aktuellen UKE-Speiseplan, zeigt automatisch den
passenden Tag, filtert nach Ernährungsform und zeigt kcal, interne und externe
Preise sowie ausgeschriebene Allergene. Ein Gericht lässt sich als Text für
YAZIO kopieren.

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

GitHub prüft die offizielle UKE-Seite montags morgens automatisch.
Das Skript sucht gezielt den Plan der aktuellen ISO-Kalenderwoche, lädt die PDF,
erzeugt die JSON-Datei und veröffentlicht die Webseite. Du musst keine PDF mehr
hochladen. Über **Actions → Speiseplan aktualisieren und veröffentlichen → Run
workflow** kannst du die Prüfung jederzeit manuell auslösen.

## Lokal testen

```bash
python -m pip install -r requirements.txt
python download_latest_pdf.py -o input/speiseplan.pdf
python uke_speiseplan.py input/speiseplan.pdf -o public/data/speiseplan.json
npm install
npm run dev
```

Anschließend die von Vite angezeigte lokale Adresse im Browser öffnen.

## Hinweis

Das Repository und die veröffentlichte Webseite sind bei einem öffentlichen
Repository ebenfalls öffentlich. Der Workflow veröffentlicht nur die erzeugten
Menüdaten, nicht die heruntergeladene PDF.
