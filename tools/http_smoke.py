#!/usr/bin/env python3
"""Start a built JAR locally and exercise a small HTTP lifecycle, with cleanup and timeouts."""
import argparse
import json
from pathlib import Path
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from toolchain_environment import save_environment
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]


def request(base, method, path, body=None, expected=200):
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(base+path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=3) as response:
            code, payload = response.status, response.read()
    except HTTPError as error:
        code, payload = error.code, error.read()
    if code != expected:
        raise RuntimeError(f"{method} {path}: expected HTTP {expected}, received {code}: {payload[:500]!r}")
    return json.loads(payload) if payload else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path, required=True)
    parser.add_argument("--java", default="java")
    args = parser.parse_args()
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    save_environment(ROOT, run_id, java=args.java, require_build=False, jar=args.jar)
    jar = args.jar.resolve()
    if not jar.is_file():
        raise SystemExit(f"Build the jar first: {jar}")
    with socket.socket() as reserve:
        reserve.bind(("127.0.0.1", 0))
        port = reserve.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    logs = ROOT/"target/smoke"
    logs.mkdir(parents=True,exist_ok=True)
    log_path = logs/(jar.stem+".log")
    with log_path.open("w",encoding="utf-8") as log:
        process = subprocess.Popen([args.java,"-jar",str(jar),f"--server.port={port}","--server.address=127.0.0.1"],
                                   stdout=log,stderr=subprocess.STDOUT)
        try:
            ready = False
            for _ in range(90):
                if process.poll() is not None:
                    raise RuntimeError(f"Server exited before readiness; see {log_path}")
                try:
                    request(base,"GET","/api/tasks/00000000-0000-0000-0000-000000000001",expected=404)
                    ready = True
                    break
                except (URLError,TimeoutError,OSError):
                    time.sleep(0.5)
            if not ready:
                raise RuntimeError(f"Server did not become ready; see {log_path}")
            task = request(base,"POST","/api/tasks",{"title":"smoke"},201)
            path = "/api/tasks/"+task["id"]
            assert request(base,"GET",path)["status"] == "TODO"
            assert request(base,"POST",path+"/complete")["status"] == "DONE"
            request(base,"POST",path+"/cancel",expected=409)
            request(base,"POST","/api/tasks",{"title":"  "},400)
            request(base,"POST","/api/tasks",{"title":"x","unexpected":1},400)
            print(f"HTTP SMOKE PASSED: {jar.name}, six API assertions; log={log_path}")
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError,RuntimeError,ValueError,AssertionError) as error:
        print(f"HTTP SMOKE FAILED: {error}",file=sys.stderr)
        sys.exit(1)
