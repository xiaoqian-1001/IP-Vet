import sys
import os
import logging
import uvicorn

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("main")

BANNER = """
CF 三方 IP - 打开浏览器 http://127.0.0.1:29999
关闭此窗口即退出。
"""

HOST = "127.0.0.1"
PORT = 29999


def main():
    print(BANNER)
    logger.info("启动本地服务 http://{}:{} ...".format(HOST, PORT))

    try:
        uvicorn.run(
            "server:app",
            host=HOST,
            port=PORT,
            log_level="warning",
            access_log=False,
        )
    except KeyboardInterrupt:
        print()
        logger.info("服务已停止")
    except Exception as e:
        logger.error("服务启动失败: {}".format(e))
        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
