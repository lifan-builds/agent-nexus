import importlib.util
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest


playwright = pytest.importorskip("playwright.sync_api")

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("nexus_browser", ROOT / "nexus.py")
nexus = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(nexus)


def test_dashboard_first_run_preview_gate_and_keyboard_tabs(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "codex"))
    for target, entry in nexus.TARGET_REGISTRY.items():
        skills = entry.get("skills")
        if skills and Path(skills).is_absolute():
            entry["skills"] = home / target / "skills"
        mcp = entry.get("mcp")
        if mcp and Path(mcp).is_absolute():
            entry["mcp"] = home / target / "mcp.json"

    server = ThreadingHTTPServer(("127.0.0.1", 0), nexus.make_dashboard_handler(tmp_path))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/"

    try:
        with playwright.sync_playwright() as session:
            try:
                browser = session.chromium.launch()
            except playwright.Error as exc:
                pytest.skip(f"Playwright browser is not installed: {exc}")
            page = browser.new_page(viewport={"width": 1280, "height": 900})
            page.goto(url)
            page.get_by_text("Start with a safe manifest").wait_for()
            assert page.get_by_role("button", name="Deploy reviewed plan").is_disabled()
            page.get_by_role("button", name="Create safe starter").click()
            page.get_by_text("Safe starter created").wait_for()
            assert (tmp_path / "nexus.personal.yml").exists()

            page.get_by_role("tab", name="Packages").focus()
            page.keyboard.press("End")
            assert page.get_by_role("tab", name="Manifest").get_attribute("aria-selected") == "true"
            assert page.locator("[data-testid=manifest-editor]").is_visible()

            page.get_by_role("button", name="Preview dry run").click()
            page.get_by_text("Preview complete").wait_for()
            assert page.get_by_role("button", name="Deploy reviewed plan").is_enabled()
            assert str(tmp_path) not in page.locator("body").inner_text()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
