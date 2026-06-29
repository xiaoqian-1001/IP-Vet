# CF 三方 IP 严选工具

Cloudflare 第三方反代 IP 严选工具，本地 B/S 架构：Python FastAPI 后端 + 内置 Web 可视化面板。

## 快速开始

```bash
cd cf-ip-scanner
pip install -r requirements.txt
python main.py
```

浏览器打开 http://127.0.0.1:29999，关闭控制台窗口即退出。

## 一键打包

**Windows**: 双击 `cf-ip-scanner/build.bat`，生成 `dist/cfipgui.exe` 单文件可执行文件。

**Linux/macOS**: `bash cf-ip-scanner/build.sh`

## 扫描参数

| 参数 | 说明 |
|------|------|
| IP 版本 | IPv4 / IPv6，默认 IPv4 |
| TLS | 开启/关闭，默认开启（HTTPS 443） |
| 数据中心 | 162 个 CF 节点可选，默认全部 |
| 端口模式 | default / wide(12端口) / random / custom |
| 期望带宽 | 最低带宽过滤阈值 Mbps，默认 50 |
| 结果数 | 输出优质 IP 数量，按带宽降序 |

## 项目结构

```
cf-ip-scanner/
├── main.py           # 入口，启动时打印固定文本
├── server.py         # FastAPI 应用 + WebSocket
├── scanner.py        # IP 拉取/CIDR 解析/并发扫描/测速
├── web_ui.py         # 内嵌深色卡片式 Web 前端
├── requirements.txt  # Python 依赖
├── build.bat         # Windows PyInstaller 打包
└── build.sh          # Linux/macOS 打包
```

## 端口占用处理

程序默认监听 `127.0.0.1:29999`，若端口被占用，修改 `main.py` 中 `PORT` 变量或释放端口：

```bash
# Windows
netstat -ano | findstr :29999

# Linux/macOS
lsof -i :29999 && kill -9 <PID>
```
