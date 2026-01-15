# 通义千问Agent项目

基于阿里通义千问和LangChain的智能Agent开发项目

## 功能特性
- 集成通义千问大模型
- 支持多种工具调用
- 可扩展的Agent架构
- 命令行交互界面

## 快速开始

### 1. 环境准备

1.1 项目结构

```
qwen-agent-project/
├── .env                    # 环境变量配置文件
├── requirements.txt        # 依赖包配置文件
├── main.py                # 主程序入口
├── config/                # 配置目录
│   ├── __init__.py
│   ├── api_keys.py       # API密钥管理
│   └── settings.py       # 项目配置
├── agents/               # Agent实现目录
│   ├── __init__.py
│   └── qwen_agent.py    # Agent核心实现
├── tools/               # 工具目录
│   ├── __init__.py
│   ├── calculator_tool.py
│   ├── time_tool.py
│   ├── file_tool.py
│   ├── web_tool.py
│   └── tool_factory.py
└── utils/               # 工具函数
    ├── __init__.py
    └── logger.py
```
可以先通过敲命令的方式创建空白项目结构，用于熟悉项目结构各个文件的功能。

1.2 安装依赖软件

注意：为避免占用C盘（windows/linux/macOS的系统盘空间有限），请将项目放在其他目录下。

1.2.1 安装Python环境

```powershell
# 1. 检查Python版本
python --version
# 推荐: Python 3.8+

# 2. 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 3. 升级pip
python -m pip install --upgrade pip
```

1.2.2 填写依赖包配置文件
requirements.txt:

```txt
# LangChain核心 - 使用这些版本确保兼容性
langchain==0.1.0
langchain-core>=0.1.0
langchain-community==0.0.10
langchainhub>=0.1.0
langchain-dashscope>=0.0.1

# 阿里云DashScope
dashscope>=1.0.0

# 基础工具
python-dotenv>=1.0.0
requests>=2.0.0
beautifulsoup4>=4.0.0
pandas>=1.0.0
```

1.2.3 使用pip命令安装依赖包

```powershell
# 1. 安装核心依赖
pip install langchain==0.1.0 langchain-core>=0.1.0

# 2. 安装社区包和DashScope集成
pip install langchain-community==0.0.10 langchain-dashscope

# 3. 安装阿里云SDK
pip install dashscope

# 4. 安装工具依赖
pip install python-dotenv requests beautifulsoup4
```

1.2.4 验证安装依赖

```powershell
# 验证关键模块是否安装成功
python -c "import dashscope; print('✅ dashscope 安装成功')"
python -c "from langchain.agents import create_react_agent; print('✅ create_react_agent 可用')"
python -c "from langchain_dashscope import ChatDashScope; print('✅ ChatDashScope 可用')"
```

1.3 api密钥配置

1.3.1 注册api密钥
 - 访问 阿里云DashScope控制台
 - 注册/登录阿里云账号
 - 在控制台创建API密钥
 - 复制API密钥

1.3.2 修改.env文件

 ```env
# 阿里云DashScope API配置
# 获取地址: https://dashscope.aliyun.com/
DASHSCOPE_API_KEY=【这里填你的API密钥，一定纯英文填写】

# 可选：代理设置
# HTTP_PROXY=http://127.0.0.1:7890
# HTTPS_PROXY=http://127.0.0.1:7890

# 项目配置
DEBUG=true
LOG_LEVEL=INFO
MAX_HISTORY=10
```

1.3.3 测试api连接

```python
# test_api.py
import os
from dotenv import load_dotenv
import dashscope

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

if not api_key or api_key == "your-api-key-here":
    print("❌ 请在 .env 文件中设置 DASHSCOPE_API_KEY")
else:
    dashscope.api_key = api_key
    response = dashscope.Generation.call(
        model="qwen-turbo",
        prompt="Hello",
        max_tokens=10
    )
    if response.status_code == 200:
        print(f"✅ API连接成功: {response.output.text}")
    else:
        print(f"❌ API连接失败: {response.code}")
```

### 2. 运行前问题处理

2.1 ### 问题1: ZeroShotAgent已被弃用问题
错误信息:
```
LangChainDeprecationWarning: The class `langchain.agents.mrkl.base.ZeroShotAgent` was deprecated in langchain 0.1.0 and will be removed in 0.2.0. Use create_react_agent instead.
```

原因分析:
- LangChain 0.1.0 版本中弃用了 ZeroShotAgent
- 新版本推荐使用 create_react_agent
解决方案:

```python
# ❌ 旧的代码（已弃用）
from langchain.agents import ZeroShotAgent
agent = ZeroShotAgent(
    llm_chain=llm,  # 这个参数已被移除
    tools=tools
)

# ✅ 新的代码（推荐）
from langchain.agents import create_react_agent
agent = create_react_agent(
    llm=llm,        # 直接传递llm
    tools=tools,
    prompt=prompt
)
```

2.2 ### 问题2: 'llm_chain' 参数错误
错误信息:

```
❌ 初始化失败: 'llm_chain'
```

原因分析:
- ZeroShotAgent 在新版本中已移除 llm_chain 参数
- API 接口已改变
解决方案:

```python
# agents/qwen_agent.py 中的正确实现
class QwenAgent:
    def __init__(self, model_name="qwen-turbo", temperature=0.3):
        # 1. 创建LLM
        self.llm = ChatDashScope(
            model=model_name,
            temperature=temperature,
            dashscope_api_key=api_key
        )
        
        # 2. 创建工具
        self.tools = self._create_tools()
        
        # 3. 使用create_react_agent创建Agent
        from langchain.agents import create_react_agent
        self.agent = create_react_agent(
            llm=self.llm,      # ✅ 直接传递llm
            tools=self.tools,
            prompt=self._create_prompt()
        )
        
        # 4. 创建执行器
        from langchain.agents import AgentExecutor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True
        )
```

2.3 提示词变量不匹配
错误信息:

```
❌ 创建Agent失败: Prompt missing required variables: {'tool_names'}
```

原因分析:
- create_react_agent 需要 {tool_names} 变量
- 但代码中使用了 {tools} 变量
解决方案:

```python
# 错误提示词模板
template = """
工具: {tools}  # ❌ 错误
...
"""

# 正确提示词模板
template = """
工具: {tool_names}  # ✅ 正确
工具描述: {tools}
...
"""
```

2.4 编码问题
错误信息:

```
UnicodeDecodeError: 'gbk' codec can't encode character...
```

原因分析:
- Windows 默认使用 GBK 编码
- Python 输出包含 UTF-8 字符
解决方案:

```python
# 在文件开头设置编码
import sys
import os

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

os.environ['PYTHONUTF8'] = '1'
```

### 3. 完整实现代码
见项目详情。相关文档可参见：
【腾讯文档】我的代理2026
https://docs.qq.com/doc/DVktORFh3VERTRm5Y
【腾讯文档】Windows 11 下基于阿里通义千问（DashScope）的 LangChain Agent 开发详细指南
https://docs.qq.com/aio/DVk5iZUxRbGh1UnNR