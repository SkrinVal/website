# Login Brute-Force Tester

Ein lokales Werkzeug, um die Brute-Force-Resistenz des Logins **deiner
eigenen** Webseite zu testen: Werden viele falsche Passwoerter blockiert
(Rate-Limiting, Account-Lockout)? Ist ein bestimmtes Passwort oder ein
4-6-stelliger PIN zu leicht zu erraten?

Die eigentlichen HTTP-Anfragen macht Python im Hintergrund (nicht der
Browser) — deshalb kannst du das Tool auf einem PC starten und ganz ohne
Upload auf deine Webseite vom Handy im selben WLAN aus bedienen.

## Wichtig — Nutzungsbedingungen

Nutze dieses Tool **ausschliesslich**:

- gegen Webseiten/Logins, deren Eigentuemer du bist, oder
- gegen Systeme, fuer die du eine ausdrueckliche schriftliche Erlaubnis zum
  Sicherheitstest hast.

Das unautorisierte Testen fremder Logins ist in den meisten Laendern
strafbar (in Deutschland z.B. nach § 202a/202c StGB, "Ausspaehen von
Daten"/Vorbereiten dazu). Die Parallelitaet ist bewusst auf maximal 20
gleichzeitige Anfragen begrenzt, damit das Tool keinen Ziel-Server
ueberlasten kann — es ist kein DoS-Werkzeug und sollte auch nicht dafuer
verwendet werden.

## Installation & Start

```bash
cd security-tools/brute-force-tester
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Die Konsole zeigt beim Start zwei Adressen an:

```
  Auf diesem PC:      http://127.0.0.1:5000
  Vom Handy im WLAN:  http://<lokale-IP>:5000
```

- Am PC selbst: `http://127.0.0.1:5000` im Browser oeffnen.
- Vom Handy: Handy mit demselben WLAN wie den PC verbinden, dann die
  angezeigte `http://<lokale-IP>:5000`-Adresse im Handy-Browser aufrufen.

Der Server ist damit fuer jeden im selben Netzwerk erreichbar — nur in
vertrauenswuerdigen Netzwerken starten (z.B. deinem Heim-WLAN), nicht in
oeffentlichen WLANs.

## Nutzung

1. Login-URL deiner Seite eintragen (die URL, an die das Login-Formular
   per POST sendet — schau dir dazu den `action`-Wert des `<form>`-Tags an).
2. Feldnamen fuer Benutzername/Passwort eintragen (die `name`-Attribute der
   `<input>`-Felder im Formular).
3. Einen Text angeben, an dem sich Erfolg oder Misserfolg erkennen laesst,
   z.B. die Fehlermeldung bei falschem Passwort, oder ein Text, der nur nach
   erfolgreichem Login erscheint (z.B. "Logout" oder "Willkommen").
4. Betriebsart waehlen:
   - **Wortliste**: eigene Passwortliste eintragen.
   - **Zahlen-PIN**: Bereich (z.B. 0 bis 999999) automatisch generieren
     lassen, optional mit fuehrenden Nullen fuer feste PIN-Laengen.
5. Tempo einstellen: Verzoegerung pro Anfrage und Parallelitaet
   (Standard 5, max. 20 gleichzeitige Anfragen).
6. Bestaetigen, dass du zum Testen berechtigt bist, und starten.

## Grenzen

- Das Tool unterstuetzt aktuell keine automatische Erkennung/Uebermittlung
  von CSRF-Tokens. Wenn dein Login-Formular ein CSRF-Token erfordert,
  schlagen alle Versuche fehl (gutes Zeichen fuer die Sicherheit deiner
  Seite!). In dem Fall musst du das Token-Handling im Skript ergaenzen.
- Erkennt HTTP 429 (Rate-Limiting) und bricht dann automatisch ab.
- Maximal 999.999 Versuche pro Lauf und maximal 20 gleichzeitige Anfragen
  (in `app.py` als `MAX_ATTEMPTS` / `MAX_CONCURRENCY` anpassbar).

## Mobile Alternative (`mobile.html`)

Es gibt auch eine reine HTML/JS-Version (`mobile.html`) ohne Python-Server.
Die macht die Anfragen direkt aus dem Handy-Browser heraus — dafuer **musst**
du sie auf derselben Domain wie die Login-Seite hosten, sonst blockiert der
Browser die Anfragen per CORS. Wenn du nichts hochladen willst oder kannst,
ist die Python-Variante hier (`app.py`) der einfachere Weg.
