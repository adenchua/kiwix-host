#!/usr/bin/env python3
"""Thin wrapper around sotoki that injects a browser-like User-Agent.

sotoki makes an HTTP GET to https://{domain}/ during initialization.
Stack Exchange / Cloudflare blocks the default python-requests UA with
a 403. Monkey-patching Session.__init__ here covers all requests sotoki
makes for the duration of the subprocess.
"""

import requests
from sotoki.__main__ import main

_FIREFOX_UA = (
    "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) "
    "Gecko/20100101 Firefox/128.0"
)

_orig_init = requests.Session.__init__


def _patched_init(self, *args, **kwargs):
    _orig_init(self, *args, **kwargs)
    self.headers["User-Agent"] = _FIREFOX_UA


requests.Session.__init__ = _patched_init

main()
