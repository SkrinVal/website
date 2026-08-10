"""
Login-Brute-Force-Tester — NUR fuer autorisierte Sicherheitstests eigener Webseiten.

Startet einen lokalen Webserver mit einem Formular. Dort traegst du die
Login-URL deiner eigenen Webseite, den Benutzernamen und entweder eine
Passwortliste oder einen Zahlen-PIN-Bereich ein. Das Tool probiert die
Passwoerter durch (optional parallel) und meldet dir, ob (und mit welchem
Passwort) der Login erfolgreich war.

Die eigentlichen HTTP-Anfragen macht Python im Hintergrund — dafuer gilt
die Browser-CORS-Sperre nicht. Du kannst dieses Tool also auf einem PC
starten und ueber dein Handy im selben WLAN aufrufen, ohne irgendetwas auf
deine eigene Webseite hochladen zu muessen.

Nutzung:
    pip install -r requirements.txt
    python app.py
    -> Am PC selbst: http://127.0.0.1:5000 oeffnen
    -> Vom Handy im selben WLAN: die beim Start angezeigte
       http://<lokale-IP>:5000 aufrufen

WICHTIG:
- Nutze das Tool ausschliesslich gegen Webseiten, die dir gehoeren oder fuer
  die du eine ausdrueckliche schriftliche Erlaubnis zum Testen hast.
- Die Parallelitaet ist bewusst auf maximal 20 gleichzeitige Anfragen
  begrenzt, damit das Tool keine echte Ueberlastung (DoS) verursachen kann.
- Der Server laeuft auf 0.0.0.0, ist also fuer jeden im selben Netzwerk
  erreichbar. Nur in vertrauenswuerdigen Netzwerken (z.B. deinem Heim-WLAN)
  starten, nicht in oeffentlichen WLANs.
"""

import queue
import socket
import threading
import time
from dataclasses import dataclass, field

import requests
from flask import Flask, render_template, request

app = Flask(__name__)

MAX_ATTEMPTS = 999_999
MAX_CONCURRENCY = 20
RESULT_ROWS_SHOWN = 25
REQUEST_TIMEOUT = 10


@dataclass
class AttemptResult:
    password: str
    status_code: object
    matched: bool


@dataclass
class RunReport:
    attempts: list = field(default_factory=list)
    found_password: str | None = None
    stopped_reason: str | None = None
    total_tried: int = 0


def build_passwords(form) -> tuple[list, str | None]:
    attack_mode = form.get("attack_mode", "wordlist")

    if attack_mode == "pin":
        try:
            pin_from = int(form.get("pin_from", "0"))
            pin_to = int(form.get("pin_to", "999999"))
        except ValueError:
            return [], "Bitte einen gueltigen PIN-Bereich angeben."

        if pin_from < 0 or pin_to > 999999 or pin_from > pin_to:
            return [], "Bitte einen gueltigen PIN-Bereich angeben (0-999999, Von <= Bis)."

        pad = form.get("pin_pad") == "on"
        try:
            pad_len = int(form.get("pin_pad_len", "6"))
        except ValueError:
            pad_len = 6

        count = min(pin_to - pin_from + 1, MAX_ATTEMPTS)
        if pad:
            passwords = [str(n).zfill(pad_len) for n in range(pin_from, pin_from + count)]
        else:
            passwords = [str(n) for n in range(pin_from, pin_from + count)]
        return passwords, None

    wordlist_raw = form.get("wordlist", "")
    passwords = [line.strip() for line in wordlist_raw.splitlines() if line.strip()][:MAX_ATTEMPTS]
    if not passwords:
        return [], "Bitte mindestens ein Passwort in der Liste angeben."
    return passwords, None


def run_bruteforce(
    login_url: str,
    username_field: str,
    password_field: str,
    username: str,
    passwords: list,
    indicator_mode: str,
    indicator_text: str,
    delay: float,
    concurrency: int,
) -> RunReport:
    report = RunReport()
    lock = threading.Lock()
    stop_event = threading.Event()

    work_queue: queue.Queue = queue.Queue()
    for pw in passwords:
        work_queue.put(pw)

    thread_local = threading.local()

    def get_session() -> requests.Session:
        if not hasattr(thread_local, "session"):
            thread_local.session = requests.Session()
        return thread_local.session

    def worker():
        session = get_session()
        while not stop_event.is_set():
            try:
                pw = work_queue.get_nowait()
            except queue.Empty:
                return

            payload = {username_field: username, password_field: pw}

            try:
                resp = session.post(login_url, data=payload, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            except requests.RequestException as exc:
                with lock:
                    report.total_tried += 1
                    if not report.stopped_reason:
                        report.stopped_reason = f"Netzwerkfehler bei Anfrage: {exc}"
                stop_event.set()
                return

            body_lower = resp.text.lower()

            with lock:
                report.total_tried += 1

                if resp.status_code == 429:
                    if not report.stopped_reason:
                        report.stopped_reason = (
                            "HTTP 429 (Too Many Requests) erhalten — Rate-Limiting ist aktiv. "
                            "Test abgebrochen (gutes Zeichen fuer die Sicherheit der Seite)."
                        )
                    report.attempts.append(AttemptResult(pw, resp.status_code, False))
                    if len(report.attempts) > RESULT_ROWS_SHOWN:
                        report.attempts.pop(0)
                    stop_event.set()
                    continue

                if indicator_mode == "success_text":
                    matched = indicator_text.lower() in body_lower
                else:
                    matched = indicator_text.lower() not in body_lower

                report.attempts.append(AttemptResult(pw, resp.status_code, matched))
                if len(report.attempts) > RESULT_ROWS_SHOWN:
                    report.attempts.pop(0)

                if matched:
                    report.found_password = pw
                    stop_event.set()
                    continue

            if delay > 0:
                time.sleep(delay)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(concurrency)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    if not report.found_password and not report.stopped_reason and report.total_tried >= MAX_ATTEMPTS:
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
        indicator_mode = request.form.get("indicator_mode", "fail_text")
        indicator_text = request.form.get("indicator_text", "").strip()

        try:
            delay = float(request.form.get("delay", "0"))
        except ValueError:
            delay = 0.0
        delay = max(delay, 0.0)

        try:
            concurrency = int(request.form.get("concurrency", "5"))
        except ValueError:
            concurrency = 5
        concurrency = max(1, min(concurrency, MAX_CONCURRENCY))

        if not confirmed:
            error = "Du musst bestaetigen, dass du zum Testen dieser Seite berechtigt bist."
        elif not login_url.startswith(("http://", "https://")):
            error = "Bitte eine gueltige Login-URL (http:// oder https://) angeben."
        elif not username:
            error = "Bitte einen Benutzernamen angeben."
        elif not indicator_text:
            error = "Bitte einen Erkennungstext angeben (siehe Hinweis im Formular)."
        else:
            passwords, build_error = build_passwords(request.form)
            if build_error:
                error = build_error
            else:
                report = run_bruteforce(
                    login_url=login_url,
                    username_field=username_field,
                    password_field=password_field,
                    username=username,
                    passwords=passwords,
                    indicator_mode=indicator_mode,
                    indicator_text=indicator_text,
                    delay=delay,
                    concurrency=concurrency,
                )

    return render_template(
        "index.html",
        report=report,
        error=error,
        max_attempts=MAX_ATTEMPTS,
        max_concurrency=MAX_CONCURRENCY,
    )


def local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


if __name__ == "__main__":
    ip = local_ip()
    print("=" * 60)
    print("Login Brute-Force Tester")
    print(f"  Auf diesem PC:      http://127.0.0.1:5000")
    print(f"  Vom Handy im WLAN:  http://{ip}:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000)
