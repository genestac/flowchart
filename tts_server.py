#!/usr/bin/env python3
"""
Local TTS proxy server for the Genestac AI Flowchart.
Accepts ?text=... and returns an MP3 audio stream via gTTS.
Runs on port 8765 alongside the main http.server on 8080.
"""
import sys
import hashlib
import os
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

CACHE_DIR = os.path.join(tempfile.gettempdir(), "tts_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

class TTSHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/tts":
            self.send_response(404)
            self.end_headers()
            return

        qs = parse_qs(parsed.query)
        text = qs.get("text", [""])[0].strip()
        if not text:
            self.send_response(400)
            self.end_headers()
            return

        # Cache key
        key = hashlib.md5(text.encode()).hexdigest()
        mp3_path = os.path.join(CACHE_DIR, f"{key}.mp3")

        if not os.path.exists(mp3_path):
            try:
                from gtts import gTTS
                tts = gTTS(text=text, lang="en", slow=False)
                tts.save(mp3_path)
            except Exception as e:
                print(f"[TTS ERROR] {e}", file=sys.stderr)
                self.send_response(500)
                self.end_headers()
                return

        self.send_response(200)
        self.send_header("Content-Type", "audio/mpeg")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "public, max-age=86400")
        with open(mp3_path, "rb") as f:
            data = f.read()
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.end_headers()

    def log_message(self, format, *args):
        print(f"[TTS] {self.address_string()} - {format % args}")

if __name__ == "__main__":
    port = 8765
    print(f"[TTS Server] Starting on http://localhost:{port}/tts?text=Hello+world")
    server = HTTPServer(("localhost", port), TTSHandler)
    server.serve_forever()
