#!/usr/bin/env python3
"""Serve the VinAssess landing page and cached or custom image URLs."""

import argparse
import json
from functools import partial
from html.parser import HTMLParser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit, unquote
from workspace_store import init_store
from workspace_api import handle_api
from rag_worker import start_worker
from assessment_runtime import start_expiry_worker
from education_store import prepare_school_demo

ROOT = Path(__file__).resolve().parents[1]


class LandingLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.routes = {"/login", "/register"}

    def handle_starttag(self, tag, attrs):
        href = dict(attrs).get("href", "")
        if tag == "a" and href.startswith("/") and not href.startswith("//"):
            route = urlsplit(href).path
            if route != "/":
                self.routes.add(route)


class MirrorServer(ThreadingHTTPServer):
    request_queue_size = 128


class MirrorHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, manifest, routes, **kwargs):
        self.manifest = manifest
        self.routes = routes
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'same-origin')
        if self.path.startswith('/workspace/') or self.path in ('/login', '/register'):
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'")
            self.send_header('X-Frame-Options', 'DENY')
        super().end_headers()

    def do_GET(self):
        parsed = urlsplit(self.path)
        if handle_api(self, 'GET', parsed.path):
            return
        normalized = unquote(parsed.path)
        if self.private_path(normalized):
            self.send_error(404)
            return
        if parsed.path in ('/login', '/register', '/workspace') or parsed.path.startswith('/workspace/') and not Path(parsed.path).suffix:
            self.path = '/workspace/index.html'
            return super().do_GET()
        if parsed.path in self.routes or parsed.path.startswith(("/blogs/", "/pages/")):
            if self.headers.get("RSC") or "_rsc" in parse_qs(parsed.query):
                # An empty prefetch tells Next.js to use browser navigation.
                self.send_response(204)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
            else:
                # Legacy mirror paths now stay within the VinAssess landing page.
                self.send_response(302)
                self.send_header("Location", "/#solutions")
                self.end_headers()
            return
        key = parsed.path
        if key == "/_next/image":
            query = parse_qs(parsed.query)
            key += "?" + urlencode({k: query[k][0] for k in ("url", "w", "q") if k in query})
        record = self.manifest["assets"].get(key)
        if record:
            path = ROOT / record["path"]
            if path.is_file():
                data = path.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", record["content_type"])
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
        if parsed.path == "/_next/image":
            # Widths generated after hydration can differ from the SSR srcset.
            original = parse_qs(parsed.query).get("url", [""])[0]
            source = urlsplit(original)
            record = self.manifest["assets"].get(source.path) if source.netloc in ("", "fervid.vn") else None
            if record:
                self.path = "/" + record["path"]
                return super().do_GET()
            if source.netloc in ("", "fervid.vn", "127.0.0.1:4173", "localhost:4173"):
                asset = (ROOT / source.path.lstrip("/")).resolve()
                if asset.is_relative_to(ROOT) and asset.is_file() and asset.suffix in {".svg", ".png", ".jpg", ".webp"}:
                    self.path = source.path
                    return super().do_GET()
        return super().do_GET()

    def do_POST(self):
        if not handle_api(self, 'POST', urlsplit(self.path).path):
            self.send_error(405)

    def do_HEAD(self):
        parsed = urlsplit(self.path)
        if parsed.path.startswith('/api/workspace/') or self.private_path(unquote(parsed.path)):
            self.send_error(405)
            return
        if parsed.path in ('/login', '/register', '/workspace') or parsed.path.startswith('/workspace/') and not Path(parsed.path).suffix:
            self.path = '/workspace/index.html'
        return super().do_HEAD()

    @staticmethod
    def private_path(path):
        parts = [p for p in path.split('/') if p]
        return any(p.startswith('.') for p in parts) or bool(parts and parts[0] in ('scripts', 'backups', 'content', 'node_modules', 'tests', 'docs', 'evaluations', 'evidence', 'reference', 'prisma', 'vendor', '.github'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=4173)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    init_store()
    prepare_school_demo()
    manifest = json.loads((ROOT / "content/landing-assets.json").read_text())
    links = LandingLinks()
    links.feed((ROOT / "index.html").read_text())
    server = MirrorServer((args.host, args.port), partial(MirrorHandler, manifest=manifest, routes=links.routes))
    worker_stop, worker_thread = start_worker()
    expiry_stop, expiry_thread = start_expiry_worker()
    print(f"VinAssess: http://{args.host}:{args.port}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        worker_stop.set()
        worker_thread.join(timeout=5)
        expiry_stop.set()
        expiry_thread.join(timeout=5)
        server.server_close()


if __name__ == "__main__":
    main()
