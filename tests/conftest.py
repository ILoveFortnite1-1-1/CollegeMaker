"""
E2E Test Infrastructure & Fixtures for College Portfolio Application.
Provides transparent HTTP / In-Process test client with cookie handling,
standard test datasets, schema assertions, and isolation utilities.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
from typing import Dict, Any, Optional, Union, List

# Add workspace root to sys.path
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

DEFAULT_BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8000")

# Known seed colleges present in test and production seed datasets
SEED_COLLEGES = {
    "mit": {"id": "166683", "name": "Massachusetts Institute of Technology", "state": "MA", "type": "private"},
    "stanford": {"id": "243744", "name": "Stanford University", "state": "CA", "type": "private"},
    "berkeley": {"id": "110635", "name": "University of California-Berkeley", "state": "CA", "type": "public"},
    "michigan": {"id": "170976", "name": "University of Michigan-Ann Arbor", "state": "MI", "type": "public"},
    "osu": {"id": "204796", "name": "Ohio State University-Main Campus", "state": "OH", "type": "public"},
    "harvard": {"id": "166027", "name": "Harvard University", "state": "MA", "type": "private"},
    "gatech": {"id": "139755", "name": "Georgia Institute of Technology-Main Campus", "state": "GA", "type": "public"},
    "uiuc": {"id": "145637", "name": "University of Illinois Urbana-Champaign", "state": "IL", "type": "public"},
    "utaustin": {"id": "228778", "name": "The University of Texas at Austin", "state": "TX", "type": "public"},
    "ucla": {"id": "110662", "name": "University of California-Los Angeles", "state": "CA", "type": "public"}
}

DEFAULT_FIT_WEIGHTS = {
    "career_outcomes": 0.25,
    "roi_value": 0.20,
    "academic_fit": 0.15,
    "admissions_fit": 0.10,
    "student_experience": 0.10,
    "academic_strength": 0.10,
    "location": 0.05,
    "cost": 0.05
}

SOURCE_PRECEDENCE = [
    "government",
    "official_institutional",
    "reputable_secondary",
    "ai_extracted",
    "model_estimate",
    "user"
]


class APIResponse:
    """Wrapper around HTTP responses for seamless test assertions."""
    def __init__(self, status_code: int, body: bytes, headers: Dict[str, str], cookies: Dict[str, str]):
        self.status_code = status_code
        self.body = body
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.cookies = cookies
        self._json_cache = None

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")

    def json(self) -> Any:
        if self._json_cache is None:
            self._json_cache = json.loads(self.text)
        return self._json_cache

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.headers.get(name.lower(), default)


class APIClient:
    """
    Opaque-box HTTP Test Client with cookie jar management,
    request routing, and session isolation.
    """
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip("/")
        self.cookie_jar: Dict[str, str] = {}
        self.default_headers: Dict[str, str] = {
            "Accept": "application/json, text/html, */*",
            "User-Agent": "CollegePortfolioE2ETestClient/1.0"
        }

    def set_cookie(self, name: str, value: str):
        self.cookie_jar[name] = value

    def clear_cookies(self):
        self.cookie_jar.clear()

    def get_cookie(self, name: str) -> Optional[str]:
        return self.cookie_jar.get(name)

    def _build_cookie_header(self, extra_cookies: Optional[Dict[str, str]] = None) -> str:
        all_cookies = dict(self.cookie_jar)
        if extra_cookies:
            all_cookies.update(extra_cookies)
        return "; ".join([f"{k}={v}" for k, v in all_cookies.items()])

    def _parse_response_cookies(self, headers: List[str]):
        for header in headers:
            parts = header.split(";")
            if parts:
                cookie_pair = parts[0].strip()
                if "=" in cookie_pair:
                    name, val = cookie_pair.split("=", 1)
                    self.cookie_jar[name.strip()] = val.strip()

    def request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Any] = None,
        data: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
        follow_redirects: bool = True
    ) -> APIResponse:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        if params:
            query_str = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query_str}"

        req_headers = dict(self.default_headers)
        if headers:
            req_headers.update(headers)

        cookie_hdr = self._build_cookie_header(cookies)
        if cookie_hdr and "Cookie" not in req_headers:
            req_headers["Cookie"] = cookie_hdr

        req_body = None
        if json_data is not None:
            req_body = json.dumps(json_data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        elif data is not None:
            if isinstance(data, str):
                req_body = data.encode("utf-8")
            else:
                req_body = data

        # Check for in-process direct app execution if server is imported
        try:
            from server.main import app
            from starlette.testclient import TestClient
            tc = TestClient(app, base_url=self.base_url, raise_server_exceptions=False)
            all_cookies = dict(self.cookie_jar)
            if cookies:
                all_cookies.update(cookies)
            resp = tc.request(
                method=method,
                url=path if path.startswith("/") else f"/{path}",
                params=params,
                json=json_data,
                content=data if req_body is not None and json_data is None else None,
                headers=req_headers,
                cookies=all_cookies,
                follow_redirects=follow_redirects,
            )
            for k, v in resp.cookies.items():
                self.cookie_jar[k] = v
            # Also parse Set-Cookie header if present
            set_cookie_headers = [v for k, v in resp.headers.items() if k.lower() == "set-cookie"]
            if set_cookie_headers:
                self._parse_response_cookies(set_cookie_headers)
            return APIResponse(resp.status_code, resp.content, dict(resp.headers), dict(self.cookie_jar))
        except Exception:
            pass

        # Fallback to standard urllib HTTP request
        req = urllib.request.Request(url, data=req_body, headers=req_headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                status_code = resp.status
                body = resp.read()
                resp_headers = dict(resp.getheaders())
                cookie_headers = [v for k, v in resp.getheaders() if k.lower() == "set-cookie"]
                self._parse_response_cookies(cookie_headers)
                return APIResponse(status_code, body, resp_headers, dict(self.cookie_jar))
        except urllib.error.HTTPError as err:
            status_code = err.code
            body = err.read()
            resp_headers = dict(err.headers.items()) if err.headers else {}
            cookie_headers = [v for k, v in resp_headers.items() if k.lower() == "set-cookie"]
            self._parse_response_cookies(cookie_headers)
            return APIResponse(status_code, body, resp_headers, dict(self.cookie_jar))
        except urllib.error.URLError as url_err:
            raise ConnectionError(f"Failed to connect to test server at {url}: {url_err.reason}")

    def get(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> APIResponse:
        return self.request("GET", path, params=params, **kwargs)

    def post(self, path: str, json: Optional[Any] = None, **kwargs) -> APIResponse:
        return self.request("POST", path, json_data=json, **kwargs)

    def put(self, path: str, json: Optional[Any] = None, **kwargs) -> APIResponse:
        return self.request("PUT", path, json_data=json, **kwargs)

    def delete(self, path: str, params: Optional[Dict[str, Any]] = None, **kwargs) -> APIResponse:
        return self.request("DELETE", path, params=params, **kwargs)


# Helper fixtures for pytest if used
try:
    import pytest

    @pytest.fixture
    def client():
        return APIClient()

    @pytest.fixture
    def session_client():
        c = APIClient()
        c.set_cookie("college_portfolio_id", "test-session-uuid-12345")
        return c

except ImportError:
    pass
