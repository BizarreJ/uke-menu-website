# UKE Menü Webseite, deployed mit GitHub Pages

Den Speiseplan der UKE Kantine kann man sich aktuell nur als pdf herunterladen [UKE Klinikgastronomie](https://www.uke.de/organisationsstruktur/tochtergesellschaften/klinik-gastronomie-eppendorf/index.html). Das ist ein bisschen nervig. 

Deshalb hier ein Workflow, bei dem die aktuelle pdf heruntergeladen und eingelesen, in eine json Datei umgewandelt und auf einer einfachen Webseite dargestellt wird. Das Skript sucht dabei gezielt den Plan der aktuellen ISO-Kalenderwoche.  
Auf der Webseite kann man den Tag und die Ernährungsform (vegan, vegetarisch, Fleisch/Fisch) auswählen. Für alle Gerichte werden die ungefähren kcal-Werte, die Preise und die Allergene angezeigt. Jede Gerichtsbeschreibung lässt sich in die Zwischenablage kopieren, um sie schnell und einfach in Kalorientracker-Apps zu übertragen.

Der Code wurde fast komplett von ChatGPT erzeugt (wer hat schon Zeit, um sowas selber zu programmieren).

URL der erzeugten Webseite: https://bizarrej.github.io/uke-menu-website/
