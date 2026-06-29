# CF 三方 IP 严选工具

Cloudflare 第三方反代 IP 严选工具，本地 B/S 架构，Python FastAPI 后端 + 内置 Web 可视化面板。

## 快速开始

### Windows

双击 `dist/cfipgui.exe` 即可运行，控制台窗口会显示启动信息，浏览器打开 http://127.0.0.1:29999 访问 Web 面板。

### Linux / macOS

```bash
# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

浏览器访问 http://127.0.0.1:29999

## 构建为单个 exe

### Windows

双击 `build.bat`，生成的 `cfipgui.exe` 在 `dist/` 目录下。

### Linux / macOS

```bash
chmod +x build.sh
./build.sh
```

## 端口占用处理

程序默认监听 `127.0.0.1:29999`。如果端口被占用，修改 `main.py` 中的 `PORT` 变量，或先释放端口：

```bash
# Windows 查找占用进程
netstat -ano | findstr :29999
# 记住 PID，在任务管理器中结束对应进程

# Linux / macOS
lsof -i :29999
kill -9 <PID>
```

## 扫描参数说明

| 参数     | 说明                                                                 |
| -------- | -------------------------------------------------------------------- |
| IP 版本  | IPv4 或 IPv6，默认 IPv4                                              |
| TLS      | 开启后使用 HTTPS 443 端口测速，关闭使用 HTTP 80 端口                 |
| 数据中心 | 筛选指定 CF 数据中心的 IP，默认全部。点击刷新拉取最新列表            |
| 端口模式 | default=默认端口, wide=12个常用端口, random=随机端口, custom=自定义  |
| 期望带宽 | 最低带宽过滤阈值，单位 Mbps，仅保留测速带宽 >= 该值的 IP              |
| 结果数   | 最终输出的优质 IP 数量，按带宽降序排列                               |

## 技术架构

- **后端**: Python 3.8+ / FastAPI / asyncio
- **前端**: 单页 HTML 内嵌于 Python 代码中
- **通信**: WebSocket 实时进度推送
- **打包**: PyInstaller --onefile 编译为单个 exe
