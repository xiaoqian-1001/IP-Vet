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
BATCH_SIZE = 200

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

    def build_pool(
        self,
        entries: List[Dict],
        ip_version: str = "ipv4",
        datacenter: str = "all",
        port_mode: str = "default",
        custom_port: Optional[int] = None,
    ) -> List[Dict]:
        pool: List[Dict] = []
        seen: Set[str] = set()

        for e in entries:
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

            pool.append({"ip": ip, "port": scan_port, "datacenter": dc})

        return pool

    async def speed_test(self, ip: str, port: int, tls: bool) -> Optional[Dict]:
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

        async def report(phase: str, data):
            if progress_callback:
                await progress_callback(phase, data)

        # Step 1: fetch
        await report("fetching", "正在拉取远程 IP 库...")
        try:
            raw_lines = await self.fetch_ip_list()
        except Exception as e:
            await report("error", f"拉取 IP 库失败: {e}")
            return []

        # Step 2: parse
        await report("parsing", "正在解析 IP 数据...")
        entries = self.parse_entries(raw_lines)
        if not entries:
            await report("error", "未解析到有效 IP 记录")
            return []

        # Step 3: build candidate pool
        pool = self.build_pool(entries, ip_version, datacenter, port_mode, custom_port)
        if not pool:
            await report("error", f"过滤后无匹配目标 ({ip_version.upper()})")
            return []

        pool_size = len(pool)
        random.shuffle(pool)

        await report("scanning", f"候选池 {pool_size} 个目标, 需收集 {result_count} 个优质 IP...")

        # Step 4: scanning loop — random draw, TLS check, speed test, collect
        qualified: List[Dict] = []
        scanned: Dict[str, bool] = {}
        scanned_count = 0
        pos = 0
        semaphore = asyncio.Semaphore(SCAN_CONCURRENCY)

        async def probe_one(target: Dict) -> Optional[Dict]:
            if self.stop_flag:
                return None
            async with semaphore:
                if self.stop_flag:
                    return None
                ip = target["ip"]
                port = target["port"]

                # Step 1: TLS / TCP connectivity check
                try:
                    ssl_ctx = self._get_ssl_context() if tls else None
                    _, writer = await asyncio.wait_for(
                        asyncio.open_connection(ip, port, ssl=ssl_ctx),
                        timeout=TCP_TIMEOUT,
                    )
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    return None

                # Step 2: speed test (opens a fresh connection)
                result = await self.speed_test(ip, port, tls)
                return result

        round_num = 0
        while len(qualified) < result_count:
            if self.stop_flag:
                break

            if pos >= pool_size:
                round_num += 1
                random.shuffle(pool)
                pos = 0
                logger.info(f"第 {round_num + 1} 轮扫描...")
                uniq_scanned = len(scanned)
                if uniq_scanned >= pool_size:
                    await report("status", f"已遍历全部 {uniq_scanned} 个不重复目标, 仅收集到 {len(qualified)}/{result_count} 个")
                    break

            batch_end = min(pos + BATCH_SIZE, pool_size)
            batch = pool[pos:batch_end]
            pos = batch_end

            tasks = [probe_one(t) for t in batch]
            raw_results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, r in enumerate(raw_results):
                if self.stop_flag:
                    break
                if isinstance(r, Exception):
                    continue

                target = batch[i]
                key = f"{target['ip']}:{target['port']}"
                if key in scanned:
                    continue
                scanned[key] = True
                scanned_count += 1

                if r is not None:
                    r["datacenter"] = target["datacenter"]
                    if r["bandwidth"] >= min_bandwidth:
                        qualified.append(r)
                        await report("found", {
                            "ip": r["ip"],
                            "port": r["port"],
                            "bandwidth": r["bandwidth"],
                            "latency": r["latency"],
                            "datacenter": r["datacenter"],
                            "found": len(qualified),
                            "target": result_count,
                            "scanned": scanned_count,
                            "pool_size": pool_size,
                        })
                        if len(qualified) >= result_count:
                            break

            await report("progress", {
                "scanned": scanned_count,
                "pool_size": pool_size,
                "found": len(qualified),
                "target": result_count,
            })

        # Step 5: sort and return
        qualified.sort(key=lambda x: x["bandwidth"], reverse=True)
        top = qualified[:result_count]

        await report("complete", {
            "results": top,
            "scanned": scanned_count,
            "pool_size": pool_size,
        })

        await self.close()
        return top
