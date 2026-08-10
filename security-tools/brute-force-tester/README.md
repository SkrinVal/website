# Login Brute-Force Tester

Ein lokales Werkzeug, um die Brute-Force-Resistenz des Logins **deiner
eigenen** Webseite zu testen: Werden viele falsche Passwoerter blockiert
(Rate-Limiting, Account-Lockout, Captcha)? Ist ein bestimmtes Passwort in
einer Wortliste zu leicht zu erraten?

## Wichtig — Nutzungsbedingungen

Nutze dieses Tool **ausschliesslich**:

- gegen Webseiten/Logins, deren Eigentuemer du bist, oder
- gegen Systeme, fuer die du eine ausdrueckliche schriftliche Erlaubnis zum
  Sicherheitstest hast.

Das unautorisierte Testen fremder Logins ist in den meisten Laendern
strafbar (in Deutschland z.B. nach § 202a/202c StGB, "Ausspaehen von
Daten"/Vorbereiten dazu). Das Tool ist bewusst so gebaut, dass es
Ziel-Server nicht ueberlastet (Verzoegerung zwischen Anfragen, begrenzte
Versuchsanzahl) — es ist kein DoS-Werkzeug und sollte auch nicht dafuer
verwendet werden.

## Installation & Start

```bash
cd security-tools/brute-force-tester
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Danach im Browser `http://127.0.0.1:5000` oeffnen.

## Nutzung

1. Login-URL deiner Seite eintragen (die URL, an die das Login-Formular
   per POST sendet — schau dir dazu den `action`-Wert des `<form>`-Tags an).
2. Feldnamen fuer Benutzername/Passwort eintragen (die `name`-Attribute der
   `<input>`-Felder im Formular).
3. Einen Text angeben, an dem sich Erfolg oder Misserfolg erkennen laesst,
   z.B. die Fehlermeldung bei falschem Passwort, oder ein Text, der nur nach
   erfolgreichem Login erscheint (z.B. "Logout" oder "Willkommen").
4. Eine Passwortliste eintragen (z.B. eine Liste haeufiger schwacher
   Passwoerter, oder ein Wortliste wie `rockyou.txt` fuer realistischere
   Tests).
5. Bestaetigen, dass du zum Testen berechtigt bist, und starten.

## Grenzen

- Das Tool unterstuetzt aktuell keine automatische Erkennung/Uebermittlung
  von CSRF-Tokens. Wenn dein Login-Formular ein CSRF-Token erfordert,
  schlagen alle Versuche fehl (gutes Zeichen fuer die Sicherheit deiner
  Seite!). In dem Fall musst du das Token-Handling im Skript ergaenzen.
- Erkennt einfache Captcha-Hinweise und HTTP 429 und bricht dann automatisch
  ab.
- Standardmaessig maximal 500 Versuche pro Lauf und mind. 0,5s Verzoegerung
  zwischen Anfragen (in `app.py` als `MAX_ATTEMPTS` / `MIN_DELAY_SECONDS`
  anpassbar).
