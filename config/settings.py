"""
项目配置文件
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any

# 项目根目录
BASE_DIR = Path(__file__).parent.parent

# 路径配置
DATA_DIR = BASE_DIR / "data"
LOG_DIR = DATA_DIR / "logs"
CACHE_DIR = DATA_DIR / "cache"
EXPORT_DIR = DATA_DIR / "exports"

# 创建必要的目录
for directory in [DATA_DIR, LOG_DIR, CACHE_DIR, EXPORT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Agent配置
AGENT_CONFIG: Dict[str, Any] = {
    "default_model": "qwen-turbo",
    "default_temperature": 0.3,
    "max_iterations": 5,
    "verbose": True,
    "handle_parsing_errors": True,
    "memory_window": 5,  # 记忆窗口大小
}

# 工具配置
TOOL_CONFIG: Dict[str, Any] = {
    "calculator": {
        "enabled": True,
        "description": "数学计算工具"
    },
    "time": {
        "enabled": True,
        "description": "时间查询工具"
    },
    "file": {
        "enabled": True,
        "description": "文件操作工具"
    },
    "web": {
        "enabled": False,  # 默认禁用，需要API密钥
        "description": "网页搜索工具"
    }
}

# 日志配置
LOG_CONFIG: Dict[str, Any] = {
    "level": os.getenv("LOG_LEVEL", "INFO"),
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    "file": LOG_DIR / "agent.log",
    "max_bytes": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

def setup_logging():
    """配置日志"""
    log_level = getattr(logging, LOG_CONFIG["level"])
    
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 清除已有的handler
    logger.handlers.clear()
    
    # 控制台handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(LOG_CONFIG["format"])
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_CONFIG["file"],
        maxBytes=LOG_CONFIG["max_bytes"],
        backupCount=LOG_CONFIG["backup_count"],
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        LOG_CONFIG["format"],
        datefmt=LOG_CONFIG["date_format"]
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger

# 初始化日志
logger = setup_logging()