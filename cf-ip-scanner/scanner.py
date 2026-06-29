import asyncio
import aiohttp
import ipaddress
import time
import ssl
import random
import logging
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

WIDE_PORTS = [80, 443, 8080, 8443, 2052, 2053, 2082, 2083, 2086, 2087, 2095, 2096]
DEFAULT_TLS_PORT = 443
DEFAULT_NO_TLS_PORT = 80

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
                logger.info(f"成功拉取 {len(lines)} 行 IP 数据")
                return lines
        except Exception as e:
            logger.error(f"拉取 IP 库失败: {e}")
            raise

    def parse_cidr(self, lines: List[str]) -> Dict[str, List[str]]:
        ipv4_ranges: Set[str] = set()
        ipv6_ranges: Set[str] = set()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                net = ipaddress.ip_network(line, strict=False)
                if net.version == 4:
                    ipv4_ranges.add(str(net))
                else:
                    ipv6_ranges.add(str(net))
            except ValueError:
                logger.warning(f"跳过无效 CIDR: {line}")
                continue

        logger.info(f"解析完成: IPv4 {len(ipv4_ranges)} 段, IPv6 {len(ipv6_ranges)} 段")
        return {"ipv4": sorted(ipv4_ranges), "ipv6": sorted(ipv6_ranges)}

    def generate_ips(
        self, ranges: List[str], max_per_range: int = 256, total_limit: int = 5000
    ) -> List[str]:
        ips: List[str] = []
        for cidr in ranges:
            if len(ips) >= total_limit:
                break
            try:
                net = ipaddress.ip_network(cidr, strict=False)
                all_hosts = (
                    list(net.hosts()) if net.num_addresses > 2 else [net.network_address]
                )
                if len(all_hosts) > max_per_range:
                    step = max(1, len(all_hosts) // max_per_range)
                    sampled = all_hosts[::step][:max_per_range]
                else:
                    sampled = all_hosts
                ips.extend(str(ip) for ip in sampled)
            except ValueError:
                continue

        random.shuffle(ips)
        ips = ips[:total_limit]
        logger.info(f"生成 {len(ips)} 个待扫描 IP")
        return ips

    def _get_ports(self, tls: bool, port_mode: str, custom_port: Optional[int]) -> List[int]:
        if port_mode == "custom" and custom_port:
            return [custom_port]
        elif port_mode == "wide":
            return list(WIDE_PORTS)
        elif port_mode == "random":
            return [random.choice(WIDE_PORTS)]
        else:
            return [DEFAULT_TLS_PORT if tls else DEFAULT_NO_TLS_PORT]

    async def scan_single(self, ip: str, port: int, tls: bool) -> Optional[Dict]:
        connect_time = time.monotonic()
        try:
            ssl_ctx = self._get_ssl_context() if tls else None
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port, ssl=ssl_ctx),
                timeout=TCP_TIMEOUT,
            )
        except Exception:
            return None

        try:
            # Measure HTTP round-trip and download speed
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
                    if data:
                        bytes_so_far = len(data)
                        if bytes_so_far >= 1024 and len(chunk) < 100:
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
            latency_ms = (time.monotonic() - connect_time) * 1000

            return {
                "ip": ip,
                "port": port,
                "bandwidth": round(bandwidth_mbps, 2),
                "latency": round(latency_ms, 1),
                "packetLoss": 0,
                "datacenter": "UNK",
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
            await progress_callback("parsing", "正在解析 CIDR 网段...")

        parsed = self.parse_cidr(raw_lines)
        ranges = parsed.get(ip_version, [])
        if not ranges:
            if progress_callback:
                await progress_callback("error", f"未找到 {ip_version.upper()} 网段")
            return []

        ips = self.generate_ips(ranges)
        ports = self._get_ports(tls, port_mode, custom_port)

        if progress_callback:
            await progress_callback(
                "scanning", f"开始扫描 {len(ips)} 个 IP ({ip_version.upper()})..."
            )

        total = len(ips) * len(ports)
        completed = 0
        valid_results: List[Dict] = []
        all_results: List[Dict] = []
        semaphore = asyncio.Semaphore(SCAN_CONCURRENCY)

        async def scan_one(ip: str, port: int):
            nonlocal completed
            if self.stop_flag:
                return
            async with semaphore:
                if self.stop_flag:
                    return
                r = await self.scan_single(ip, port, tls)
                completed += 1
                if r:
                    all_results.append(r)
                    valid_results.append(r)
                if progress_callback and completed % 10 == 0:
                    await progress_callback("progress", {
                        "current": completed,
                        "total": total,
                        "ip": ip,
                        "port": port,
                        "valid": len(valid_results),
                    })

        tasks = []
        for ip in ips:
            if self.stop_flag:
                break
            for port in ports:
                tasks.append(scan_one(ip, port))

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
                "total_count": len(all_results),
            })

        await self.close()
        return top_results
