"""
Login-Brute-Force-Tester — NUR fuer autorisierte Sicherheitstests eigener Webseiten.

Startet einen lokalen Webserver mit einem Formular. Dort traegst du die
Login-URL deiner eigenen Webseite, den Benutzernamen und eine Passwortliste
ein. Das Tool probiert die Passwoerter der Reihe nach durch und meldet dir,
ob (und mit welchem Passwort) der Login erfolgreich war.

Nutzung:
    pip install -r requirements.txt
    python app.py
    -> im Browser http://127.0.0.1:5000 oeffnen

WICHTIG:
- Nutze das Tool ausschliesslich gegen Webseiten, die dir gehoeren oder fuer
  die du eine ausdrueckliche schriftliche Erlaubnis zum Testen hast.
- Das Tool baut absichtlich eine Verzoegerung zwischen den Versuchen ein und
  begrenzt die maximale Anzahl an Versuchen, um Zielserver nicht zu
  ueberlasten (kein DoS-Werkzeug).
"""

import time
from dataclasses import dataclass, field

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

MAX_ATTEMPTS = 500
MIN_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT = 10


@dataclass
class AttemptResult:
    password: str
    status_code: int
    elapsed: float
    matched: bool


@dataclass
class RunReport:
    attempts: list = field(default_factory=list)
    found_password: str | None = None
    stopped_reason: str | None = None
    total_tried: int = 0


def run_bruteforce(
    login_url: str,
    username_field: str,
    password_field: str,
    username: str,
    extra_fields: dict,
    passwords: list,
    indicator_mode: str,
    indicator_text: str,
    delay: float,
) -> RunReport:
    report = RunReport()
    session = requests.Session()

    delay = max(delay, MIN_DELAY_SECONDS)
    passwords = passwords[:MAX_ATTEMPTS]

    for pw in passwords:
        payload = dict(extra_fields)
        payload[username_field] = username
        payload[password_field] = pw

        try:
            resp = session.post(login_url, data=payload, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        except requests.RequestException as exc:
            report.stopped_reason = f"Netzwerkfehler bei Anfrage: {exc}"
            break

        body_lower = resp.text.lower()

        if "captcha" in body_lower:
            report.stopped_reason = (
                "Captcha im Antworttext erkannt — Ziel schuetzt sich aktiv. "
                "Test abgebrochen (gutes Zeichen fuer die Sicherheit der Seite)."
            )
            report.attempts.append(AttemptResult(pw, resp.status_code, resp.elapsed.total_seconds(), False))
            report.total_tried += 1
            break

        if resp.status_code == 429:
            report.stopped_reason = (
                "HTTP 429 (Too Many Requests) erhalten — Rate-Limiting ist aktiv. "
                "Test abgebrochen (gutes Zeichen fuer die Sicherheit der Seite)."
            )
            report.attempts.append(AttemptResult(pw, resp.status_code, resp.elapsed.total_seconds(), False))
            report.total_tried += 1
            break

        if indicator_mode == "success_text":
            matched = indicator_text.lower() in body_lower
        else:
            matched = indicator_text.lower() not in body_lower

        result = AttemptResult(pw, resp.status_code, resp.elapsed.total_seconds(), matched)
        report.attempts.append(result)
        report.total_tried += 1

        if matched:
            report.found_password = pw
            break

        time.sleep(delay)

    if report.total_tried >= MAX_ATTEMPTS and not report.found_password and not report.stopped_reason:
        report.stopped_reason = f"Maximale Versuchsanzahl ({MAX_ATTEMPTS}) erreicht."

    return report


@app.route("/", methods=["GET", "POST"])
def index():
    report = None
    error = None

    if request.method == "POST":
        confirmed = request.form.get("confirm_authorized") == "on"
        login_url = request.form.get("login_url", "").strip()
        username_field = request.form.get("username_field", "username").strip() or "username"
        password_field = request.form.get("password_field", "password").strip() or "password"
        username = request.form.get("username", "").strip()
        wordlist_raw = request.form.get("wordlist", "")
        indicator_mode = request.form.get("indicator_mode", "fail_text")
        indicator_text = request.form.get("indicator_text", "").strip()
        try:
            delay = float(request.form.get("delay", "1"))
        except ValueError:
            delay = 1.0

        if not confirmed:
            error = "Du musst bestaetigen, dass du zum Testen dieser Seite berechtigt bist."
        elif not login_url.startswith(("http://", "https://")):
            error = "Bitte eine gueltige Login-URL (http:// oder https://) angeben."
        elif not username:
            error = "Bitte einen Benutzernamen angeben."
        elif not indicator_text:
            error = "Bitte einen Erkennungstext angeben (siehe Hinweis im Formular)."
        else:
            passwords = [line.strip() for line in wordlist_raw.splitlines() if line.strip()]
            if not passwords:
                error = "Bitte mindestens ein Passwort in der Liste angeben."
            else:
                report = run_bruteforce(
                    login_url=login_url,
                    username_field=username_field,
                    password_field=password_field,
                    username=username,
                    extra_fields={},
                    passwords=passwords,
                    indicator_mode=indicator_mode,
                    indicator_text=indicator_text,
                    delay=delay,
                )

    return render_template("index.html", report=report, error=error, max_attempts=MAX_ATTEMPTS)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
