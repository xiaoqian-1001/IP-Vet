import asyncio
import aiohttp
import time
import ssl
import random
import logging
import re
from typing import List, Dict, Optional, Set

logger = logging.getLogger("scanner")

IP_LIST_URL = "https://raw.githubusercontent.com/yu-929/Selected-by-Monte-Carlo/refs/heads/main/ip.txt"

CF_DATACENTERS = [
    "AMS", "ARN", "ATH", "ATL", "BEG", "BKK", "BLR", "BNA", "BNE", "BOG",
    "BOM", "BOS", "BRU", "BUD", "BUF", "BWN", "CDG", "CGK", "CGP", "CMB",
    "CMH", "CNX", "CPH", "CPT", "CUR", "DAC", "DAR", "DEL", "DEN", "DFW",
    "DME", "DOH", "DUB", "DUS", "DXB", "EDI", "EZE", "FCO", "FOC", "FOR",
    "FRA", "GIG", "GMP", "GND", "GRU", "GUA", "GYD", "HAM", "HAN", "HEL",
    "HKG", "HNL", "HYD", "IAH", "ICN", "IND", "ISB", "IST", "ITM", "JAX",
    "JIB", "JNB", "INB", "KBP", "KEF", "KHI", "KIV", "KJA", "KIX", "KTM",
    "KUL", "KWI", "LAD", "LAS", "LAX", "LCA", "LHE", "LHR", "LIM", "LIS",
    "LOS", "LUX", "MAA", "MAD", "MAN", "MBA", "MCI", "MCT", "MDE", "MEL",
    "MEM", "MEX", "MFE", "MIA", "MLE", "MNL", "MRS", "MRU", "MSP", "MUC",
    "MXP", "NBO", "NCL", "NRT", "NUQ", "OKC", "ORD", "OSL", "OTP", "PDX",
    "PER", "PHL", "PHX", "PIT", "PNH", "POA", "PRG", "PTY", "QRO", "REC",
    "RIX", "ROB", "RUH", "SAL", "SAN", "SCL", "SEA", "SFO", "SGN", "SIN",
    "SJC", "SJO", "SKG", "SOF", "STL", "SVX", "SYD", "TBS", "TLH", "TLL",
    "TLV", "TPA", "TPE", "TUN", "TXL", "UBN", "UIO", "ULN", "VCP", "VIE",
    "VNO", "WAW", "WLG", "YEG", "YOW", "YUL", "YVR", "YWG", "YYC", "YYZ",
    "ZAG", "ZRH",
]

SCAN_CONCURRENCY = 200
TCP_TIMEOUT = 3
SPEED_TEST_SIZE = 65536
SPEED_TEST_TIMEOUT = 8

HTTP_REQUEST_TEMPLATE = (
    "GET / HTTP/1.1\r\n"
    "Host: speed.cloudflare.com\r\n"
    "User-Agent: CF-IP-Scanner/1.0\r\n"
    "Accept: */*\r\n"
    "Connection: close\r\n"
    "\r\n"
)

ENTRY_PATTERN = re.compile(r"^((?:\d{1,3}\.){3}\d{1,3}|(?:[0-9a-fA-F:]+)):(\d+)(?:#(\w+))?$")


class Scanner:
    def __init__(self):
        self.stop_flag = False
        self.session: Optional[aiohttp.ClientSession] = None
        self._ssl_context: Optional[ssl.SSLContext] = None

    def _get_ssl_context(self) -> ssl.SSLContext:
        if self._ssl_context is None:
            self._ssl_context = ssl.create_default_context()
            self._ssl_context.check_hostname = False
            self._ssl_context.verify_mode = ssl.CERT_NONE
        return self._ssl_context

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            connector = aiohttp.TCPConnector(limit=0, force_close=True)
            timeout = aiohttp.ClientTimeout(total=10, connect=TCP_TIMEOUT)
            self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self.session

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch_ip_list(self) -> List[str]:
        logger.info("正在从远程拉取 IP 库...")
        session = await self._get_session()
        try:
            async with session.get(IP_LIST_URL, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                if resp.status != 200:
                    raise Exception(f"HTTP {resp.status}")
                text = await resp.text()
                lines = [
                    line.strip()
                    for line in text.splitlines()
                    if line.strip() and not line.startswith("#")
                ]
                logger.info(f"成功拉取 {len(lines)} 行数据")
                return lines
        except Exception as e:
            logger.error(f"拉取 IP 库失败: {e}")
            raise

    def parse_entries(self, lines: List[str]) -> List[Dict]:
        entries: List[Dict] = []
        dc_set: Set[str] = set()
        for line in lines:
            m = ENTRY_PATTERN.match(line)
            if not m:
                continue
            ip = m.group(1)
            port = int(m.group(2))
            dc = m.group(3) or "UNK"
            entries.append({"ip": ip, "port": port, "datacenter": dc})
            if dc != "UNK":
                dc_set.add(dc)

        logger.info(f"解析完成: {len(entries)} 条 IP 记录, {len(dc_set)} 个数据中心")
        return entries

    def get_datacenters(self, entries: List[Dict]) -> List[str]:
        dcs = sorted(set(e["datacenter"] for e in entries if e["datacenter"] != "UNK"))
        dc_map = {dc: True for dc in dcs}
        for dc in CF_DATACENTERS:
            if dc not in dc_map:
                dcs.append(dc)
        return sorted(dcs)

    def filter_entries(
        self,
        entries: List[Dict],
        ip_version: str = "ipv4",
        datacenter: str = "all",
        port_mode: str = "default",
        custom_port: Optional[int] = None,
        max_count: int = 5000,
    ) -> List[Dict]:
        result: List[Dict] = []
        seen: Set[str] = set()

        for e in entries:
            if len(result) >= max_count:
                break

            ip = e["ip"]
            port = e["port"]
            dc = e["datacenter"]

            is_v4 = ":" not in ip
            if ip_version == "ipv4" and not is_v4:
                continue
            if ip_version == "ipv6" and is_v4:
                continue

            if datacenter != "all" and dc.upper() != datacenter.upper():
                continue

            scan_port = port
            if port_mode == "custom" and custom_port:
                scan_port = custom_port

            key = f"{ip}:{scan_port}"
            if key in seen:
                continue
            seen.add(key)

            result.append({"ip": ip, "port": scan_port, "datacenter": dc})

        random.shuffle(result)
        logger.info(f"过滤后 {len(result)} 个待扫描目标")
        return result

    async def scan_single(self, ip: str, port: int, tls: bool) -> Optional[Dict]:
        connect_start = time.monotonic()
        try:
            ssl_ctx = self._get_ssl_context() if tls else None
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port, ssl=ssl_ctx),
                timeout=TCP_TIMEOUT,
            )
        except Exception:
            return None

        try:
            req_start = time.monotonic()
            writer.write(HTTP_REQUEST_TEMPLATE.encode())
            await writer.drain()

            data = bytearray()
            headers_done = False
            buf = bytearray()
            try:
                while True:
                    chunk = await asyncio.wait_for(
                        reader.read(4096), timeout=SPEED_TEST_TIMEOUT
                    )
                    if not chunk:
                        break
                    buf.extend(chunk)
                    if not headers_done:
                        idx = buf.find(b"\r\n\r\n")
                        if idx >= 0:
                            data = bytearray(buf[idx + 4:])
                            headers_done = True
                            buf = bytearray()
                    else:
                        data = buf
                        buf = bytearray()
                    if len(data) >= SPEED_TEST_SIZE:
                        break
                    if data and len(data) >= 1024 and len(chunk) < 100:
                        break
            except asyncio.TimeoutError:
                pass

            download_duration = time.monotonic() - req_start
            if download_duration <= 0:
                return None

            total_bytes = len(data) + (len(buf) if not headers_done else 0)
            if total_bytes == 0:
                return None

            bandwidth_mbps = (total_bytes * 8) / (download_duration * 1_000_000)
            latency_ms = (time.monotonic() - connect_start) * 1000

            return {
                "ip": ip,
                "port": port,
                "bandwidth": round(bandwidth_mbps, 2),
                "latency": round(latency_ms, 1),
                "packetLoss": 0,
                "datacenter": None,
                "passed": True,
            }
        except Exception:
            return None
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def run_scan(
        self,
        ip_version: str = "ipv4",
        tls: bool = True,
        datacenter: str = "all",
        min_bandwidth: float = 50,
        result_count: int = 5,
        port_mode: str = "default",
        custom_port: Optional[int] = None,
        progress_callback=None,
    ) -> List[Dict]:
        self.stop_flag = False

        if progress_callback:
            await progress_callback("fetching", "正在拉取远程 IP 库...")

        try:
            raw_lines = await self.fetch_ip_list()
        except Exception as e:
            if progress_callback:
                await progress_callback("error", f"拉取 IP 库失败: {e}")
            return []

        if progress_callback:
            await progress_callback("parsing", "正在解析 IP 数据...")

        entries = self.parse_entries(raw_lines)
        if not entries:
            if progress_callback:
                await progress_callback("error", "未解析到有效 IP 记录")
            return []

        targets = self.filter_entries(entries, ip_version, datacenter, port_mode, custom_port)
        if not targets:
            if progress_callback:
                await progress_callback("error", f"过滤后无匹配目标 ({ip_version.upper()})")
            return []

        if progress_callback:
            await progress_callback(
                "scanning",
                f"开始扫描 {len(targets)} 个目标 ({ip_version.upper()}{', DC=' + datacenter if datacenter != 'all' else ''})...",
            )

        total = len(targets)
        completed = 0
        valid_results: List[Dict] = []
        semaphore = asyncio.Semaphore(SCAN_CONCURRENCY)

        async def scan_one(target: Dict):
            nonlocal completed
            if self.stop_flag:
                return
            async with semaphore:
                if self.stop_flag:
                    return
                r = await self.scan_single(target["ip"], target["port"], tls)
                completed += 1
                if r:
                    r["datacenter"] = target["datacenter"]
                    valid_results.append(r)
                if progress_callback and completed % 10 == 0:
                    await progress_callback("progress", {
                        "current": completed,
                        "total": total,
                        "ip": target["ip"],
                        "port": target["port"],
                        "valid": len(valid_results),
                    })

        tasks = [scan_one(t) for t in targets]
        await asyncio.gather(*tasks, return_exceptions=True)

        if progress_callback:
            await progress_callback("progress", {
                "current": completed,
                "total": total,
                "ip": "--",
                "port": 0,
                "valid": len(valid_results),
            })

        filtered = [
            r for r in valid_results if r.get("passed") and r["bandwidth"] >= min_bandwidth
        ]
        filtered.sort(key=lambda x: x["bandwidth"], reverse=True)
        top_results = filtered[:result_count]

        if progress_callback:
            await progress_callback("complete", {
                "results": top_results,
                "total_scanned": completed,
                "valid_count": len(valid_results),
                "total_count": completed,
            })

        await self.close()
        return top_results
