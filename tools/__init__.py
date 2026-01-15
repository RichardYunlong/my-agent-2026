"""
工具包初始化
"""
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# 工具基类
class BaseTool:
    """工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    def validate_input(self, input_data: Any) -> bool:
        """验证输入"""
        return True
    
    def execute(self, *args, **kwargs) -> Any:
        """执行工具"""
        raise NotImplementedError
    
    def __call__(self, *args, **kwargs) -> str:
        """调用工具"""
        try:
            if self.validate_input(kwargs):
                result = self.execute(*args, **kwargs)
                self.logger.info(f"工具 {self.name} 执行成功")
                return str(result)
            else:
                error_msg = f"工具 {self.name} 输入验证失败"
                self.logger.error(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"工具 {self.name} 执行失败: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return error_msg