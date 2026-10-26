"""Measure the live admin login without printing credentials or cookies."""

import http.cookiejar
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def request(opener, request):
    started = time.monotonic()
    try:
        response = opener.open(request, timeout=20)
    except urllib.error.HTTPError as error:
        response = error
    elapsed = time.monotonic() - started
    return response, elapsed


def main(domain):
    repo = Path(__file__).resolve().parents[2]
    password = (repo / "backend" / ".admin-initial-password").read_text(encoding="utf-8").strip()
    url = f"https://{domain}/admin/login/?next=/admin/"
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()), NoRedirect())

    response, elapsed = request(opener, urllib.request.Request(url))
    html = response.read().decode("utf-8", "replace")
    match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html)
    print(f"GET login: HTTP {response.code}, {elapsed:.2f} s")
    if not match:
        raise RuntimeError("CSRF token not found in login form")

    data = urllib.parse.urlencode({
        "csrfmiddlewaretoken": match.group(1),
        "username": "admin",
        "password": password,
        "next": "/admin/",
    }).encode()
    response, elapsed = request(opener, urllib.request.Request(url, data=data, headers={"Referer": url}))
    print(f"POST login: HTTP {response.code}, {elapsed:.2f} s, redirect {response.headers.get('Location', '-')}")

    success_page = response.code == 200 and b"RAMP_LOGIN_OK" in response.read()
    if response.code in (301, 302, 303) or success_page:
        response, elapsed = request(opener, urllib.request.Request(f"https://{domain}/admin/"))
        print(f"GET admin: HTTP {response.code}, {elapsed:.2f} s")


if __name__ == "__main__":
    if len(sys.argv) != 2 or not re.fullmatch(r"[a-z0-9.-]+", sys.argv[1]):
        raise SystemExit("Usage: python diagnose_admin_http.py domain.webtm.ru")
    main(sys.argv[1])
