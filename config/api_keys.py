"""
API密钥配置管理
"""
import os
from typing import Dict, Optional, List
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class APIConfig:
    """API配置管理类"""
    
    # ========== API密钥配置 ==========
    DASHSCOPE_API_KEY: Optional[str] = os.getenv("DASHSCOPE_API_KEY")
    SERPAPI_API_KEY: Optional[str] = os.getenv("SERPAPI_API_KEY")
    
    # ========== 代理配置 ==========
    HTTP_PROXY: Optional[str] = os.getenv("HTTP_PROXY")
    HTTPS_PROXY: Optional[str] = os.getenv("HTTPS_PROXY")
    
    # ========== 模型配置 ==========
    # 可用模型列表
    MODEL_CONFIGS: Dict[str, Dict] = {
        "qwen-turbo": {
            "model": "qwen-turbo",
            "description": "通义千问轻量版，响应快，成本低",
            "max_tokens": 2000,
            "temperature_range": (0.1, 1.0),
            "recommended_for": ["开发测试", "简单对话"]
        },
        "qwen-plus": {
            "model": "qwen-plus",
            "description": "通义千问增强版，效果更好",
            "max_tokens": 4000,
            "temperature_range": (0.1, 1.0),
            "recommended_for": ["生产环境", "复杂任务"]
        },
        "qwen-max": {
            "model": "qwen-max",
            "description": "通义千问最大版，最强能力",
            "max_tokens": 6000,
            "temperature_range": (0.1, 1.0),
            "recommended_for": ["关键任务", "高质量输出"]
        }
    }
    
    # 默认配置
    DEFAULT_MODEL: str = "qwen-turbo"
    DEFAULT_TEMPERATURE: float = 0.3
    DEFAULT_MAX_TOKENS: int = 2000
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证配置是否完整"""
        errors = []
        
        if not cls.DASHSCOPE_API_KEY:
            errors.append("❌ 未设置DASHSCOPE_API_KEY环境变量")
        
        if errors:
            print("\n".join(errors))
            print("\n请从阿里云DashScope控制台获取API密钥：https://dashscope.aliyun.com/")
            print("然后在.env文件中添加：DASHSCOPE_API_KEY=你的密钥")
            return False
        
        return True
    
    @classmethod
    def get_model_info(cls, model_name: str = None) -> Dict:
        """获取模型信息"""
        if model_name is None:
            model_name = cls.DEFAULT_MODEL
        
        if model_name in cls.MODEL_CONFIGS:
            return cls.MODEL_CONFIGS[model_name].copy()
        else:
            raise ValueError(f"不支持的模型: {model_name}")
    
    @classmethod
    def list_available_models(cls) -> List[str]:
        """获取可用模型列表"""
        return list(cls.MODEL_CONFIGS.keys())

# 创建配置实例
api_config = APIConfig()

# 设置代理（如果有）
if api_config.HTTP_PROXY:
    os.environ['HTTP_PROXY'] = api_config.HTTP_PROXY
if api_config.HTTPS_PROXY:
    os.environ['HTTPS_PROXY'] = api_config.HTTPS_PROXY