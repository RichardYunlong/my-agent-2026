"""
通义千问Agent核心实现
使用create_react_agent替代被弃用的ZeroShotAgent
"""
import sys
import os
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# 导入LangChain相关模块
from langchain_dashscope import ChatDashScope
from langchain.agents import create_react_agent, AgentExecutor
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import BaseTool, Tool
from langchain.prompts import PromptTemplate
from langchain.callbacks import StdOutCallbackHandler
from langchain import hub

# 导入配置和工具
from config.api_keys import api_config
from config.settings import logger, AGENT_CONFIG
from tools.tool_factory import tool_factory


class QwenAgent:
    """通义千问Agent类 - 使用create_react_agent"""
    
    def __init__(
        self,
        model_name: str = None,
        temperature: float = None,
        verbose: bool = None,
        max_iterations: int = None
    ):
        """初始化Agent
        
        Args:
            model_name: 模型名称
            temperature: 温度参数
            verbose: 是否显示详细日志
            max_iterations: 最大迭代次数
        """
        logger.info("🚀 初始化千问Agent...")
        
        # 验证配置
        if not api_config.validate_config():
            raise ValueError("API配置验证失败")
        
        # 设置参数
        self.model_name = model_name or AGENT_CONFIG["default_model"]
        self.temperature = temperature or AGENT_CONFIG["default_temperature"]
        self.verbose = verbose or AGENT_CONFIG["verbose"]
        self.max_iterations = max_iterations or AGENT_CONFIG["max_iterations"]
        
        # 初始化组件
        self.llm = None
        self.tools = []
        self.memory = None
        self.agent = None
        self.agent_executor = None
        
        # 初始化历史记录
        self.conversation_history = []
        self.tool_usage_stats = {}
        
        # 初始化所有组件
        self._initialize_llm()
        self._initialize_tools()
        self._initialize_memory()
        self._initialize_agent()
        
        logger.info(f"✅ 千问Agent初始化完成 - 模型: {self.model_name}")
        logger.info(f"🔧 可用工具: {[tool.name for tool in self.tools]}")
    
    def _initialize_llm(self):
        """初始化语言模型"""
        try:
            model_info = api_config.get_model_info(self.model_name)
            
            self.llm = ChatDashScope(
                model=self.model_name,
                temperature=self.temperature,
                max_tokens=model_info.get("max_tokens", 2000),
                dashscope_api_key=api_config.DASHSCOPE_API_KEY,
                streaming=False,
                request_timeout=30
            )
            
            logger.info(f"✅ LLM初始化成功: {self.model_name}")
            
        except Exception as e:
            logger.error(f"❌ LLM初始化失败: {e}")
            raise
    
    def _initialize_tools(self):
        """初始化工具"""
        try:
            self.tools = tool_factory.get_all_tools()
            
            # 初始化使用统计
            for tool in self.tools:
                self.tool_usage_stats[tool.name] = 0
            
            logger.info(f"✅ 工具初始化成功: {len(self.tools)} 个工具")
            
        except Exception as e:
            logger.error(f"❌ 工具初始化失败: {e}")
            # 创建基本工具作为回退
            self.tools = self._create_basic_tools()
    
    def _create_basic_tools(self) -> List[Tool]:
        """创建基本工具（回退方案）"""
        from datetime import datetime
        
        def calculator(expression: str) -> str:
            """计算器工具"""
            try:
                # 安全限制
                dangerous = ['import', 'exec', 'eval', '__', 'open', 'os.', 'sys.']
                expr_lower = expression.lower()
                for d in dangerous:
                    if d in expr_lower:
                        return f"安全限制：不允许包含 '{d}' 的表达式"
                
                result = eval(expression, {"__builtins__": {}})
                return f"计算结果: {result}"
            except Exception as e:
                return f"计算错误: {e}"
        
        def get_time(query: str = "") -> str:
            """时间工具"""
            now = datetime.now()
            if "星期" in query or "周" in query:
                weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
                return f"今天是 {now.strftime('%Y年%m月%d日')}，{weekdays[now.weekday()]}"
            else:
                return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        
        def list_files(path: str = ".") -> str:
            """文件列表工具"""
            try:
                import os
                files = os.listdir(path if path else ".")
                if not files:
                    return f"目录 '{path}' 为空"
                return f"目录 '{path}' 中的文件: {', '.join(files[:10])}"
            except Exception as e:
                return f"列出文件失败: {e}"
        
        basic_tools = [
            Tool(
                name="calculator",
                func=calculator,
                description="计算数学表达式。输入示例: '2+3 * 4' 或 '10/2'"
            ),
            Tool(
                name="time_tool",
                func=get_time,
                description="获取当前时间、日期和星期几。输入示例: '现在几点了？' 或 '今天星期几？'"
            ),
            Tool(
                name="file_lister",
                func=list_files,
                description="列出目录中的文件。输入: 目录路径（可选，默认为当前目录）"
            )
        ]
        
        return basic_tools
    
    def _initialize_memory(self):
        """初始化记忆"""
        try:
            self.memory = ConversationBufferWindowMemory(
                memory_key="chat_history",
                k=AGENT_CONFIG["memory_window"],
                return_messages=True
            )
            logger.info("✅ 记忆初始化成功")
        except Exception as e:
            logger.error(f"⚠️ 记忆初始化失败: {e}")
            self.memory = None
    
    def _initialize_agent(self):
        """初始化Agent - 使用create_react_agent"""
        try:
            # 获取提示词
            prompt = self._get_react_prompt()
            
            # 使用create_react_agent（替代ZeroShotAgent）
            self.agent = create_react_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            # 创建Agent执行器
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                memory=self.memory,
                verbose=self.verbose,
                handle_parsing_errors=AGENT_CONFIG["handle_parsing_errors"],
                max_iterations=self.max_iterations,
                early_stopping_method="generate",
                callbacks=[StdOutCallbackHandler()] if self.verbose else []
            )
            
            logger.info("✅ Agent执行器初始化成功（使用create_react_agent）")
            
        except Exception as e:
            logger.error(f"❌ Agent初始化失败: {e}")
            raise
    
    def _get_react_prompt(self) -> PromptTemplate:
        """获取ReAct提示词 - 修复变量名问题"""
        try:
            # 尝试从LangChain Hub获取官方提示词
            prompt = hub.pull("hwchase17/react-chat")
            logger.info("✅ 使用LangChain Hub官方提示词")
            return prompt
        except Exception as e:
            logger.warning(f"⚠️ 无法获取Hub提示词: {e}")
            logger.info("使用本地提示词模板")
            
            # 本地提示词模板 - 确保变量名正确
            template = """你是一个AI助手，可以使用工具来帮助用户解决问题。

你有以下工具可以使用：
{tool_names}

每个工具的描述：
{tools}

使用以下格式：
Question: 用户的问题
Thought: 我需要思考如何解决这个问题
Action: 要使用的工具名称
Action Input: 工具的输入
Observation: 工具返回的结果
...（这个思考/行动/观察可以重复多次）
Thought: 我现在有足够的信息来回答用户了
Final Answer: 对用户问题的最终回答

请记住：
1. 如果用户用中文提问，请用中文回答
2. 如果可以使用工具，尽量使用工具
3. 如果工具返回错误，请尝试其他方法
4. 保持回答专业、准确、有帮助

之前的对话：
{chat_history}

现在开始！

Question: {input}
{agent_scratchpad}"""
            
            return PromptTemplate.from_template(template)
    
    def query(self, user_input: str) -> Dict[str, Any]:
        """执行用户查询
        
        Args:
            user_input: 用户输入的问题
            
        Returns:
            dict: 包含回答和元数据的字典
        """
        if not user_input or not user_input.strip():
            return {
                "success": False,
                "error": "输入不能为空",
                "response": "请输入您的问题"
            }
        
        logger.info(f"📥 收到查询: {user_input[:50]}...")
        
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            # 准备输入
            inputs = {"input": user_input}
            if self.memory:
                inputs["chat_history"] = self.memory.chat_memory.messages
            
            # 执行Agent
            response = self.agent_executor.invoke(inputs)
            
            # 计算耗时
            elapsed_time = (datetime.now() - start_time).total_seconds()
            
            # 获取回答
            answer = response.get("output", "")
            
            # 记录对话历史
            self.conversation_history.append({
                "timestamp": start_time.isoformat(),
                "user": user_input,
                "assistant": answer,
                "elapsed_time": elapsed_time,
                "model": self.model_name
            })
            
            # 更新工具使用统计
            self._update_tool_stats()
            
            logger.info(f"✅ 查询完成 - 耗时: {elapsed_time:.2f}秒")
            
            return {
                "success": True,
                "response": answer,
                "elapsed_time": elapsed_time,
                "model": self.model_name,
                "timestamp": start_time.isoformat()
            }
            
        except Exception as e:
            error_msg = f"查询过程中出错: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            return {
                "success": False,
                "error": error_msg,
                "response": f"抱歉，处理您的请求时出现了问题: {str(e)[:100]}"
            }
    
    def _update_tool_stats(self):
        """更新工具使用统计"""
        # 这里可以扩展为解析中间步骤
        pass
    
    def batch_query(self, queries: List[str]) -> List[Dict[str, Any]]:
        """批量查询"""
        results = []
        total_queries = len(queries)
        
        logger.info(f"🔢 开始批量处理 {total_queries} 个查询")
        
        for i, query in enumerate(queries, 1):
            logger.info(f"📊 处理第 {i}/{total_queries} 个查询: {query[:50]}...")
            
            result = self.query(query)
            results.append(result)
            
            if not result["success"]:
                logger.warning(f"❌ 第 {i} 个查询失败: {result.get('error')}")
        
        logger.info(f"✅ 批量处理完成 - 成功: {sum(1 for r in results if r['success'])}/{total_queries}")
        
        return results
    
    def get_history(self, limit: int = 10) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def get_tool_stats(self) -> Dict[str, int]:
        """获取工具使用统计"""
        return self.tool_usage_stats.copy()
    
    def get_available_tools(self) -> List[Dict]:
        """获取可用工具列表"""
        tools_info = []
        for tool in self.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "usage_count": self.tool_usage_stats.get(tool.name, 0)
            })
        
        return tools_info
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        if self.memory:
            self.memory.clear()
        logger.info("🧹 对话历史已清空")
    
    def change_model(self, model_name: str, temperature: float = None):
        """切换模型"""
        if model_name not in api_config.list_available_models():
            raise ValueError(f"不支持的模型: {model_name}")
        
        old_model = self.model_name
        self.model_name = model_name
        
        if temperature is not None:
            self.temperature = temperature
        
        # 重新初始化
        self._initialize_llm()
        self._initialize_agent()
        
        logger.info(f"🔄 模型已切换: {old_model} -> {model_name}")


# 兼容的SimpleQwenAgent（供现有代码使用）
class SimpleQwenAgent(QwenAgent):
    """简化版千问Agent - 兼容现有代码"""
    
    def __init__(self, model_name: str = "qwen-turbo", temperature: float = 0.3):
        """初始化简化版Agent"""
        print("🤖 初始化简化版千问Agent...")
        super().__init__(
            model_name=model_name,
            temperature=temperature,
            verbose=True,
            max_iterations=3
        )


# 创建Agent实例的函数
def create_default_agent(use_simple: bool = False) -> QwenAgent:
    """创建默认Agent实例
    
    Args:
        use_simple: 是否使用简化版
    """
    if use_simple:
        return SimpleQwenAgent()
    else:
        return QwenAgent()


def test_agent():
    """测试Agent功能"""
    print("🧪 测试Agent功能...")
    
    try:
        agent = create_default_agent(use_simple=True)
        
        test_cases = [
            "计算一下 2+3 * 4 等于多少？",
            "现在几点了？",
            "今天星期几？",
            "列出当前目录的文件"
        ]
        
        for query in test_cases:
            print(f"\n📝 测试查询: {query}")
            result = agent.query(query)
            
            if result["success"]:
                print(f"✅ 成功 ({result['elapsed_time']:.2f}秒)")
                response = result["response"]
                if len(response) > 100:
                    response = response[:100] + "..."
                print(f"💡 回答: {response}")
            else:
                print(f"❌ 失败: {result.get('error')}")
        
        print("\n🎉 测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False