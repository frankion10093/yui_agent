import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# -------------------------- 1. 定义颜色常量（ANSI 转义码） --------------------------
# 格式：\033[显示方式;前景色;背景色m  （0m 表示重置颜色）
COLOR_CODES = {
    logging.DEBUG: "\033[0;36m",  # 天蓝色（DEBUG）
    logging.INFO: "\033[0;32m",  # 绿色（INFO）
    logging.WARNING: "\033[0;33m",  # 黄色（WARNING）
    logging.ERROR: "\033[0;31m",  # 红色（ERROR）
    logging.CRITICAL: "\033[0;35m",  # 洋红色（CRITICAL）
    "RESET": "\033[0m"  # 重置颜色
}


# -------------------------- 2. 自定义彩色格式化器 --------------------------
class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # 为当前日志级别获取对应的颜色码
        color = COLOR_CODES.get(record.levelno, COLOR_CODES["RESET"])
        # 给日志级别名添加颜色（如 [INFO] 变成绿色）
        record.levelname = f"{color}{record.levelname}{COLOR_CODES['RESET']}"
        # 给日志消息添加颜色（可选：也可以只给级别名加颜色）
        # record.msg = f"{color}{record.msg}{COLOR_CODES['RESET']}"
        # 调用父类的 format 方法完成最终格式化
        return super().format(record)


# -------------------------- 3. 初始化日志器（含彩色输出） --------------------------
def setup_logger():
    # 自定义日志器名称（避免冲突）
    logger = logging.getLogger("MY_APP_LOGGER")

    # 已初始化则直接返回（避免重复添加处理器）
    if logger.handlers:
        return logger

    # 基础配置
    logger.setLevel(logging.DEBUG)
    logger.propagate = False  # 禁用传播到 root 日志器

    # -------------------------- 控制台处理器（彩色输出） --------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    # 彩色格式化器（仅控制台用）
    colored_formatter = ColoredFormatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(colored_formatter)
    logger.addHandler(console_handler)

    # -------------------------- 文件处理器（无颜色，避免乱码） --------------------------

    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)),"logs")

    os.makedirs(log_dir, exist_ok=True)
    file_handler = RotatingFileHandler(
        filename=os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    # 文件用普通格式化器（无颜色码）
    file_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


# -------------------------- 4. Windows 终端兼容处理 --------------------------
# Windows 终端默认不支持 ANSI 颜色，需通过 colorama 启用
if sys.platform == "win32":
    try:
        from colorama import init

        init(autoreset=True)  # 自动重置颜色，避免后续输出受影响
    except ImportError:
        # 未安装 colorama 则提示（可选）
        print("提示：Windows 终端需安装 colorama 以显示彩色日志 → pip install colorama", file=sys.stderr)

# 模块导入时初始化，全局复用
logger = setup_logger()