"""
通义千问Agent核心实现
"""
import sys
import os
import json
import math
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# 添加项目根目录到路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

# 先检查并安装必要依赖
def ensure_dependencies():
    """确保必要的依赖已安装"""
    try:
        import dashscope
        from dotenv import load_dotenv
        from langchain_dashscope import ChatDashScope
        from langchain.agents import AgentExecutor, create_react_agent
        from langchain.memory import ConversationBufferWindowMemory
        from langchain.tools import Tool
        from langchain import hub
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("正在尝试安装必要依赖...")
        import subprocess
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", 
                                  "dashscope", "python-dotenv", "langchain-dashscope"])
            print("✅ 依赖安装完成，请重新运行程序")
        except:
            print("❌ 自动安装失败，请手动运行:")
            print("pip install dashscope python-dotenv langchain-dashscope")
        return False

# 检查依赖
if not ensure_dependencies():
    sys.exit(1)

# 现在导入
from dotenv import load_dotenv
load_dotenv()

from langchain_dashscope import ChatDashScope
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import Tool
from langchain import hub

from config.api_keys import api_config


# ==================== 工具定义 ====================
class CalculatorTool:
    """计算器工具"""
    def __init__(self):
        self.name = "calculator"
        self.description = "用于数学计算。支持加减乘除、平方、开方等。示例：'2+3 * 4' 或 'sqrt(16)'"
    
    def run(self, expression: str) -> str:
        try:
            # 安全限制
            dangerous = ['import', 'exec', 'eval', '__', 'open', 'os.', 'sys.']
            expr_lower = expression.lower()
            for d in dangerous:
                if d in expr_lower:
                    return f"安全限制：不允许包含 '{d}' 的表达式"
            
            # 替换常见函数
            expr = expression
            expr = expr.replace('^', '**')
            expr = expr.replace('×', '*')
            expr = expr.replace('÷', '/')
            
            # 计算
            result = eval(expr, {"__builtins__": {}, "math": math})
            
            # 格式化结果
            if isinstance(result, float):
                if result.is_integer():
                    result = int(result)
                else:
                    result = round(result, 6)
            
            return f"计算结果: {result}"
        except ZeroDivisionError:
            return "错误：除数不能为零"
        except Exception as e:
            return f"计算错误: {str(e)}"


class TimeTool:
    """时间工具"""
    def __init__(self):
        self.name = "time_tool"
        self.description = "获取当前时间和日期信息。可以查询现在几点、今天星期几等。"
    
    def run(self, query: str = "") -> str:
        now = datetime.now()
        
        if not query or "现在" in query or "当前" in query or "时间" in query:
            return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"
        elif "星期" in query or "周" in query:
            weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
            weekday = weekdays[now.weekday()]
            return f"今天是 {now.strftime('%Y年%m月%d日')}，{weekday}"
        elif "日期" in query or "天" in query:
            return f"当前日期: {now.strftime('%Y年%m月%d日')}"
        else:
            return f"当前时间: {now.strftime('%Y年%m月%d日 %H:%M:%S')}"


class FileListTool:
    """文件列表工具"""
    def __init__(self):
        self.name = "list_files"
        self.description = "列出指定目录下的文件和文件夹。输入目录路径，如 '.' 表示当前目录。"
    
    def run(self, directory: str = ".") -> str:
        try:
            if not directory or directory.strip() == "":
                directory = "."
            
            if not os.path.exists(directory):
                return f"目录不存在: {directory}"
            
            items = os.listdir(directory)
            if not items:
                return f"目录为空: {directory}"
            
            # 分类
            dirs = []
            files = []
            
            for item in items:
                item_path = os.path.join(directory, item)
                if os.path.isdir(item_path):
                    dirs.append(f"📁 {item}/")
                else:
                    files.append(f"📄 {item}")
            
            # 构建结果
            result_parts = []
            if dirs:
                result_parts.append("目录:")
                result_parts.extend(dirs[:5])
            
            if files:
                if result_parts:
                    result_parts.append("")
                result_parts.append("文件:")
                result_parts.extend(files[:5])
            
            return "\n".join(result_parts)
            
        except Exception as e:
            return f"列出目录时出错: {str(e)}"


def get_all_tools():
    """获取所有工具实例"""
    return [
        CalculatorTool(),
        TimeTool(),
        FileListTool()
    ]


# ==================== Agent 类 ====================
class QwenAgent:
    """通义千问Agent类"""
    
    def __init__(self, model_name: str = "qwen-turbo", temperature: float = 0.3):
        """初始化Agent
        
        Args:
            model_name: 模型名称，支持 qwen-turbo, qwen-plus, qwen-max
            temperature: 温度参数，控制回答的随机性
        """
        print("🔧 正在初始化千问Agent...")
        
        # 验证配置
        if not api_config.validate_config():
            raise ValueError("API配置验证失败，请检查.env文件")
        
        self.model_name = model_name
        self.temperature = temperature
        
        # 1. 初始化模型
        print("  初始化千问模型...")
        self.llm = ChatDashScope(
            model=model_name,
            temperature=temperature,
            dashscope_api_key=api_config.DASHSCOPE_API_KEY
        )
        
        # 2. 初始化工具
        print("  初始化工具...")
        simple_tools = get_all_tools()
        self.tools = []
        for tool in simple_tools:
            self.tools.append(
                Tool(
                    name=tool.name,
                    func=tool.run,
                    description=tool.description
                )
            )
        
        # 3. 初始化Agent执行器
        print("  创建Agent执行器...")
        self.agent_executor = self._create_agent_executor()
        
        # 4. 初始化对话历史
        self.conversation_history = []
        
        print(f"✅ 千问Agent初始化完成！")
        print(f"   模型: {model_name}")
        print(f"   可用工具: {[tool.name for tool in self.tools]}")
        print("-" * 50)
    
    def _create_agent_executor(self):
        """创建Agent执行器"""
        # 创建提示词
        prompt_template = """你是一个AI助手，可以调用各种工具来帮助用户解决问题。

你可以使用的工具:
{tools}

使用以下格式:
问题: 用户的问题
思考: 我需要如何解决这个问题
行动: 要使用的工具名称
行动输入: 工具的输入
观察: 工具返回的结果
... (这个思考/行动/观察可以重复多次)
思考: 我现在可以给出最终答案了
最终答案: 对用户问题的最终回答

如果用户用中文提问，请用中文回答。

开始!

之前的对话:
{chat_history}

问题: {input}
{agent_scratchpad}"""
        
        from langchain.prompts import PromptTemplate
        prompt = PromptTemplate.from_template(prompt_template)
        
        # 创建内存
        memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=2,
            return_messages=True
        )
        
        # 创建ReAct Agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # 创建执行器
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def query(self, user_input: str) -> Dict[str, Any]:
        """执行用户查询"""
        if not user_input or not user_input.strip():
            return {"success": False, "error": "输入不能为空"}
        
        print(f"\n{'='*50}")
        print(f"👤 用户: {user_input}")
        print(f"{'='*50}")
        
        try:
            # 记录开始时间
            start_time = datetime.now()
            
            # 执行查询
            response = self.agent_executor.invoke({
                "input": user_input
            })
            
            # 计算耗时
            elapsed = (datetime.now() - start_time).total_seconds()
            
            # 获取回答
            answer = response.get("output", "")
            
            # 记录历史
            self.conversation_history.append({
                "time": start_time.strftime("%H:%M:%S"),
                "user": user_input,
                "assistant": answer,
                "elapsed": f"{elapsed:.2f}s"
            })
            
            return {
                "success": True,
                "response": answer,
                "elapsed": elapsed,
                "model": self.model_name
            }
            
        except Exception as e:
            error_msg = f"查询出错: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "response": f"处理请求时出错: {str(e)[:100]}"
            }
    
    def get_history(self, limit: int = 5) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def clear_history(self):
        """清空对话历史"""
        self.conversation_history.clear()
        print("✅ 对话历史已清空")


# ==================== 命令行界面 ====================
def cli_interface():
    """命令行交互界面"""
    print("\n" + "="*60)
    print("    通义千问Agent - 命令行交互界面")
    print("="*60)
    print("🎯 可用命令:")
    print("  /help     - 显示帮助")
    print("  /history  - 查看对话历史")
    print("  /clear    - 清空对话历史")
    print("  /tools    - 查看可用工具")
    print("  /exit     - 退出程序")
    print("="*60)
    print("💡 尝试提问:")
    print("  • 计算一下2的10次方是多少？")
    print("  • 现在几点了？")
    print("  • 列出当前目录的文件")
    print("="*60)
    
    try:
        # 创建Agent实例
        agent = QwenAgent(
            model_name="qwen-turbo",
            temperature=0.3
        )
        
        while True:
            try:
                # 获取用户输入
                user_input = input("\n💬 请输入您的问题: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.startswith('/'):
                    cmd = user_input.lower().strip()
                    
                    if cmd in ['/exit', '/quit', 'exit', 'quit']:
                        print("\n👋 再见！感谢使用千问Agent")
                        break
                    
                    elif cmd == '/help':
                        print("\n📋 可用命令:")
                        print("  /help     - 显示此帮助信息")
                        print("  /history  - 查看最近的对话历史")
                        print("  /clear    - 清空对话历史")
                        print("  /tools    - 查看可用的工具列表")
                        print("  /exit     - 退出程序")
                        continue
                    
                    elif cmd == '/history':
                        history = agent.get_history(5)
                        if history:
                            print(f"\n📚 最近 {len(history)} 条对话:")
                            for i, item in enumerate(history, 1):
                                print(f"\n{i}. [{item['time']}]")
                                print(f"   用户: {item['user']}")
                                print(f"   AI: {item['assistant'][:80]}..." 
                                      if len(item['assistant']) > 80 
                                      else f"   AI: {item['assistant']}")
                                print(f"   耗时: {item['elapsed']}")
                        else:
                            print("\n📭 暂无对话历史")
                        continue
                    
                    elif cmd == '/clear':
                        agent.clear_history()
                        continue
                    
                    elif cmd == '/tools':
                        print("\n🛠️  可用工具:")
                        for tool in agent.tools:
                            print(f"  • {tool.name}: {tool.description[:60]}...")
                        continue
                    
                    else:
                        print(f"\n⚠️  未知命令: {user_input}")
                        print("输入 /help 查看可用命令")
                        continue
                
                # 处理普通查询
                result = agent.query(user_input)
                
                if result["success"]:
                    print(f"\n{'='*50}")
                    print(f"🤖 AI回答 ({result['elapsed']:.2f}秒):")
                    print(f"{result['response']}")
                    print(f"{'='*50}")
                else:
                    print(f"\n❌ 错误: {result.get('error', '未知错误')}")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️  检测到中断操作")
                confirm = input("是否退出程序？(y/n): ").lower().strip()
                if confirm in ['y', 'yes', '是']:
                    print("👋 再见！")
                    break
            
            except Exception as e:
                print(f"\n❌ 处理过程中出错: {str(e)}")
                
    except Exception as e:
        print(f"\n❌ Agent初始化失败: {str(e)}")
        print("\n🔧 可能的原因和解决方案:")
        print("1. ❌ API密钥错误")
        print("   检查.env文件中的DASHSCOPE_API_KEY是否正确")
        print("   获取地址: https://dashscope.aliyun.com/")
        print()
        print("2. ❌ 网络连接问题")
        print("   检查网络连接，或尝试设置代理:")
        print("   在.env文件中添加:")
        print("   HTTP_PROXY=http://127.0.0.1:7890")
        print("   HTTPS_PROXY=http://127.0.0.1:7890")
        print()
        print("3. ❌ 依赖包未安装")
        print("   运行: pip install dashscope python-dotenv langchain-dashscope")
        print()
        print("4. ❌ Python环境问题")
        print("   尝试创建虚拟环境:")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   pip install -r requirements.txt")


# 导出函数
__all__ = ['QwenAgent', 'cli_interface']


# 直接运行测试
if __name__ == "__main__":
    print("🚀 直接运行千问Agent...")
    cli_interface()