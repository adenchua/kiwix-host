#!/usr/bin/env python3
"""Thin wrapper around sotoki that bypasses Cloudflare TLS fingerprinting.

sotoki fetches Stack Exchange URLs during initialization and image download.
Cloudflare blocks Python's default TLS fingerprint (JA3) regardless of
User-Agent. curl_cffi uses libcurl with BoringSSL to produce a real Firefox
TLS handshake, bypassing bot detection for all HTTP methods and sessions.
"""

import sys
from urllib.parse import urlparse

import requests
import requests.sessions
import requests.exceptions
from curl_cffi import requests as cffi_requests
from requests.structures import CaseInsensitiveDict
from sotoki.__main__ import main

_IMPERSONATE = "firefox"
_OrigSession = requests.Session  # save before patching
_fallback_session = _OrigSession()  # singleton; avoids per-call socket leak


class _CompatResponse:
    """Wraps a curl_cffi response to satisfy requests-compatible type hints.

    curl_cffi returns its own Headers and Response types that fail beartype
    checks in zimscraperlib (e.g. stream_file expects CaseInsensitiveDict).
    This proxy converts only what's needed and delegates everything else.
    """

    def __init__(self, cffi_response):
        object.__setattr__(self, "_resp", cffi_response)
        object.__setattr__(
            self, "headers", CaseInsensitiveDict(dict(cffi_response.headers))
        )

    def __getattr__(self, name):
        return getattr(object.__getattribute__(self, "_resp"), name)

    def __setattr__(self, name, value):
        if name == "headers":
            object.__setattr__(self, name, value)
        else:
            setattr(object.__getattribute__(self, "_resp"), name, value)

    def __bool__(self):
        return bool(object.__getattribute__(self, "_resp"))

    def raise_for_status(self):
        resp = object.__getattribute__(self, "_resp")
        if resp.status_code >= 400:
            print(f"[wrapper] HTTP {resp.status_code} for {resp.url}", file=sys.stderr, flush=True)
            raise requests.exceptions.HTTPError(
                f"HTTP Error {resp.status_code}: {resp.reason}",
                response=resp,
            )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        object.__getattribute__(self, "_resp").__exit__(*args)


class _FirefoxSession(cffi_requests.Session):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("impersonate", _IMPERSONATE)
        super().__init__(*args, **kwargs)
        self.adapters = {}  # compatibility with code that inspects session.adapters

    def mount(self, prefix, adapter):
        self.adapters[prefix] = adapter  # store for compat; curl_cffi ignores urllib3 adapters

    def request(self, method, url, **kwargs):
        # Inject Referer = origin if absent — CDNs block sub-resource requests
        # (images, favicons) that arrive without a referring page.
        headers = dict(kwargs.get("headers") or {})
        lower_keys = {k.lower() for k in headers}
        if "referer" not in lower_keys:
            parsed = urlparse(url)
            if parsed.scheme and parsed.netloc:
                headers["Referer"] = f"{parsed.scheme}://{parsed.netloc}/"
                kwargs["headers"] = headers

        try:
            resp = _CompatResponse(super().request(method, url, **kwargs))
        except Exception as exc:
            # curl_cffi raises its own error types (e.g. TLS downgrade on some CDNs).
            # Fall back to standard requests for hosts that reject BoringSSL's TLS.
            if not type(exc).__module__.startswith("curl_cffi"):
                raise
            return _fallback_session.request(method, url, **kwargs)
        # Also fall back on 403 — some CDNs reject BoringSSL at the app layer.
        if resp.status_code == 403:
            fallback = _fallback_session.request(method, url, **kwargs)
            if fallback.status_code < 400:
                return fallback
        return resp


# Patch module-level functions (requests.get, requests.head, etc.)
for _name in ("get", "head", "post", "put", "patch", "delete", "options"):
    _cffi_fn = getattr(cffi_requests, _name, None)
    if _cffi_fn:
        def _make_patched(fn):
            def _patched(url, **kwargs):
                kwargs.setdefault("impersonate", _IMPERSONATE)
                return fn(url, **kwargs)
            return _patched
        setattr(requests, _name, _make_patched(_cffi_fn))

# Patch Session so session-based calls also use Firefox TLS
requests.Session = _FirefoxSession
requests.sessions.Session = _FirefoxSession

main()
