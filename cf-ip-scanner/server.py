import asyncio
import json
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from web_ui import WEB_UI_HTML
from scanner import Scanner, CF_DATACENTERS

logger = logging.getLogger("server")

app = FastAPI(title="CF 三方 IP", docs_url=None, redoc_url=None)


@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(content=WEB_UI_HTML)


@app.get("/api/datacenters")
async def get_datacenters():
    return {"datacenters": sorted(CF_DATACENTERS)}


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    scanner = Scanner()
    scan_task: asyncio.Task | None = None

    async def progress_callback(phase: str, data):
        try:
            await ws.send_json({"type": phase, "data": data})
        except Exception:
            pass

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if msg.get("type") == "start_scan":
                if scan_task and not scan_task.done():
                    scanner.stop_flag = True
                    scan_task.cancel()
                    try:
                        await scan_task
                    except asyncio.CancelledError:
                        pass

                config = msg.get("config", {})
                scanner.stop_flag = False

                scan_task = asyncio.create_task(
                    scanner.run_scan(
                        ip_version=config.get("ipVersion", "ipv4"),
                        tls=config.get("tls", True),
                        datacenter=config.get("datacenter", "all"),
                        min_bandwidth=config.get("minBandwidth", 50),
                        result_count=config.get("resultCount", 5),
                        port_mode=config.get("portMode", "default"),
                        custom_port=config.get("customPort"),
                        progress_callback=progress_callback,
                    )
                )

            elif msg.get("type") == "stop_scan":
                scanner.stop_flag = True
                if scan_task and not scan_task.done():
                    scan_task.cancel()

    except WebSocketDisconnect:
        pass
    finally:
        scanner.stop_flag = True
        if scan_task and not scan_task.done():
            scan_task.cancel()
        await scanner.close()
