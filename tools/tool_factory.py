"""
工具工厂
"""
from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool as LangchainTool
from langchain.tools import Tool

from .calculator_tool import calculator_tool
from .time_tool import time_tool
from .file_tool import file_tool
from .web_tool import web_tool

class ToolFactory:
    """工具工厂类"""
    
    def __init__(self):
        self._tools = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有工具"""
        # 计算器工具
        self._tools["calculator"] = Tool(
            name=calculator_tool.name,
            description=calculator_tool.description[:200],  # 限制描述长度
            func=lambda x: calculator_tool.execute(expression=x)
        )
        
        # 时间工具
        self._tools["time_tool"] = Tool(
            name=time_tool.name,
            description=time_tool.description[:200],
            func=lambda x: time_tool.execute(query=x)
        )
        
        # 文件工具
        self._tools["file_tool"] = Tool(
            name=file_tool.name,
            description=file_tool.description[:200],
            func=lambda x: file_tool.execute(operation="list", path=x) if x else file_tool.execute(operation="list")
        )
        
        # 网页工具
        self._tools["web_tool"] = Tool(
            name=web_tool.name,
            description=web_tool.description[:200],
            func=lambda x: web_tool.execute(operation="fetch", url=x)
        )
    
    def get_tool(self, tool_name: str) -> Optional[LangchainTool]:
        """获取指定工具"""
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> List[LangchainTool]:
        """获取所有工具"""
        return list(self._tools.values())
    
    def get_tool_names(self) -> List[str]:
        """获取所有工具名称"""
        return list(self._tools.keys())
    
    def get_tool_descriptions(self) -> str:
        """获取工具描述"""
        descriptions = []
        for name, tool in self._tools.items():
            descriptions.append(f"🔧 {name}: {tool.description[:100]}...")
        return "\n".join(descriptions)
    
    def create_custom_tool(self, name: str, description: str, func) -> LangchainTool:
        """创建自定义工具"""
        tool = Tool(name=name, description=description[:200], func=func)
        self._tools[name] = tool
        return tool

# 创建工具工厂实例
tool_factory = ToolFactory()