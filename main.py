"""
主程序入口
解决ZeroShotAgent弃用问题
"""
import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def setup_environment():
    """设置运行环境"""
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    os.environ['PYTHONUTF8'] = '1'
    os.environ['PYTHONIOENCODING'] = 'utf-8'

def check_dependencies():
    """检查依赖"""
    print("🔍 检查依赖...")
    print("="*50)
    
    # 正确的导入名映射
    required_packages = [
        ("dashscope", "dashscope"),
        ("python-dotenv", "dotenv"),
        ("langchain-core", "langchain_core"),
        ("langchain", "langchain"),
        ("langchain-community", "langchain_community"),
        ("langchain-dashscope", "langchain_dashscope"),
    ]
    
    missing_packages = []
    
    for pkg_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {pkg_name}")
        except ImportError as e:
            print(f"❌ {pkg_name} - 错误: {e}")
            missing_packages.append(pkg_name)
    
    if missing_packages:
        print(f"\n⚠️ 缺少依赖: {', '.join(missing_packages)}")
        print("\n请运行以下命令安装:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_config():
    """检查配置文件"""
    print("\n🔧 检查配置...")
    
    env_file = project_root / ".env"
    if not env_file.exists():
        print("❌ 未找到 .env 文件")
        print("正在创建 .env 文件模板...")
        
        env_content = """# 阿里云DashScope API配置
# 获取地址: https://dashscope.aliyun.com/
DASHSCOPE_API_KEY=your-api-key-here

# 项目配置
DEBUG=true
LOG_LEVEL=INFO
MAX_HISTORY=10
"""
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(env_content)
        
        print("✅ 已创建 .env 文件")
        print("请编辑此文件，填入您的API密钥")
        return False
    
    # 加载环境变量
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key or api_key == "your-api-key-here":
        print("❌ 请在 .env 文件中设置 DASHSCOPE_API_KEY")
        return False
    
    print(f"✅ API密钥: {api_key[:10]}...")
    return True

def test_api_connection():
    """测试API连接"""
    print("\n🔗 测试API连接...")
    
    try:
        import dashscope
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("DASHSCOPE_API_KEY")
        
        dashscope.api_key = api_key
        
        # 简单测试
        response = dashscope.Generation.call(
            model="qwen-turbo",
            prompt="Hello",
            max_tokens=10
        )
        
        if response.status_code == 200:
            print(f"✅ API连接成功")
            return True
        else:
            print(f"❌ API调用失败: {response.code} - {response.message}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {e}")
        return False

def interactive_agent_mode():
    """交互式Agent模式"""
    print("\n" + "="*60)
    print("🤖 通义千问Agent - 交互式命令行")
    print("="*60)
    print("注意：已修复ZeroShotAgent弃用问题")
    print("现在使用 create_react_agent")
    print("="*60)
    print("命令:")
    print("  /help     - 显示帮助")
    print("  /history  - 查看对话历史")
    print("  /tools    - 查看可用工具")
    print("  /clear    - 清空对话历史")
    print("  /exit     - 退出程序")
    print("="*60)
    print("💡 工具使用示例:")
    print("  • 计算: 计算一下2+3 * 4")
    print("  • 时间: 现在几点了？今天星期几？")
    print("  • 文件: 列出当前目录")
    print("="*60)
    
    try:
        from agents import SimpleQwenAgent
        
        print("正在初始化Agent（使用create_react_agent）...")
        agent = SimpleQwenAgent(
            model_name="qwen-turbo",
            temperature=0.3
        )
        
        print("✅ Agent初始化完成！")
        
        # 主循环
        while True:
            try:
                user_input = input("\n💬 请输入您的问题: ").strip()
                
                if not user_input:
                    continue
                
                # 处理特殊命令
                if user_input.startswith('/'):
                    cmd = user_input.lower()
                    
                    if cmd in ['/exit', '/quit', 'exit', 'quit']:
                        print("👋 再见！")
                        break
                    
                    elif cmd == '/help':
                        print("\n📋 可用命令:")
                        print("  /help     - 显示此帮助信息")
                        print("  /history  - 查看最近的对话历史")
                        print("  /tools    - 查看可用的工具列表")
                        print("  /clear    - 清空对话历史")
                        print("  /exit     - 退出程序")
                        continue
                    
                    elif cmd == '/history':
                        history = agent.get_history(10)
                        if history:
                            print(f"\n📚 最近对话 ({len(history)} 条):")
                            for i, item in enumerate(history, 1):
                                print(f"\n{i}. [{item['timestamp'][11:19]}]")
                                print(f"   用户: {item['user'][:50]}...")
                                response = item['assistant']
                                if len(response) > 50:
                                    response = response[:50] + "..."
                                print(f"   AI: {response}")
                                print(f"   耗时: {item['elapsed_time']:.2f}秒")
                        else:
                            print("\n📭 暂无对话历史")
                        continue
                    
                    elif cmd == '/tools':
                        tools = agent.get_available_tools()
                        if tools:
                            print(f"\n🛠️ 可用工具 ({len(tools)} 个):")
                            for tool in tools:
                                usage = tool['usage_count']
                                print(f"  • {tool['name']}: {tool['description'][:60]}... (使用次数: {usage})")
                        else:
                            print("\n🛠️ 暂无可用工具")
                        continue
                    
                    elif cmd == '/clear':
                        agent.clear_history()
                        print("\n🧹 对话历史已清空")
                        continue
                    
                    else:
                        print(f"❌ 未知命令: {user_input}")
                        print("输入 /help 查看可用命令")
                        continue
                
                # 处理普通查询
                print("⏳ 正在处理...")
                result = agent.query(user_input)
                
                if result["success"]:
                    print(f"\n{'='*60}")
                    print(f"🤖 AI回答 ({result['elapsed_time']:.2f}秒):")
                    print(f"{result['response']}")
                    print(f"{'='*60}")
                else:
                    print(f"\n❌ 错误: {result.get('error', '未知错误')}")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ 检测到中断操作")
                confirm = input("是否退出程序？(y/n): ").lower().strip()
                if confirm in ['y', 'yes', '是']:
                    print("👋 再见！")
                    break
            except EOFError:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 处理过程中出错: {e}")
                
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 可能的原因和解决方案:")
        print("1. ❌ API密钥无效")
        print("   检查.env文件中的DASHSCOPE_API_KEY是否正确")
        print("   获取地址: https://dashscope.aliyun.com/")

def direct_chat_mode():
    """直接聊天模式（不使用LangChain Agent）"""
    print("\n💬 直接聊天模式")
    print("="*60)
    
    try:
        import dashscope
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv("DASHSCOPE_API_KEY")
        
        dashscope.api_key = api_key
        
        print("输入 'exit' 退出")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n你: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', '退出']:
                    print("👋 再见！")
                    break
                
                print("AI: ", end="", flush=True)
                
                response = dashscope.Generation.call(
                    model="qwen-turbo",
                    prompt=user_input,
                    max_tokens=1000
                )
                
                if response.status_code == 200:
                    print(response.output.text)
                else:
                    print(f"❌ 错误: {response.code}")
                    
            except KeyboardInterrupt:
                print("\n👋 再见！")
                break
            except Exception as e:
                print(f"\n❌ 错误: {e}")
                
    except Exception as e:
        print(f"❌ 聊天模式失败: {e}")

def test_simple_agent():
    """测试简单Agent"""
    print("\n🧪 测试简单Agent功能...")
    
    try:
        from agents import test_agent
        test_agent()
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通义千问智能Agent系统')
    parser.add_argument('--mode', type=str, default='cli',
                       choices=['cli', 'direct', 'test'],
                       help='运行模式: cli(Agent模式), direct(直接聊天), test(测试)')
    parser.add_argument('--check', action='store_true', help='只检查环境不运行')
    
    args = parser.parse_args()
    
    # 设置环境
    setup_environment()
    
    print("="*60)
    print("    🚀 通义千问智能Agent系统")
    print("="*60)
    print("修复问题: ZeroShotAgent已被弃用")
    print("使用: create_react_agent")
    print("="*60)
    
    # 检查依赖
    if not check_dependencies():
        if not args.check:
            input("\n按Enter键退出...")
        return
    
    # 检查配置
    if not check_config():
        if not args.check:
            input("\n按Enter键退出...")
        return
    
    # 测试API连接
    if not test_api_connection():
        if not args.check:
            choice = input("\nAPI连接测试失败，是否继续？(y/n): ").lower().strip()
            if choice not in ['y', 'yes', '是']:
                return
    
    # 如果只检查环境
    if args.check:
        print("\n✅ 环境检查完成")
        return
    
    # 根据模式运行
    if args.mode == 'direct':
        direct_chat_mode()
    elif args.mode == 'test':
        test_simple_agent()
    else:  # 默认cli模式
        interactive_agent_mode()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 程序已退出")
    except Exception as e:
        print(f"\n❌ 程序运行出错: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 建议:")
        print("1. 检查.env文件中的API密钥")
        print("2. 运行: pip install -r requirements.txt")
        input("\n按Enter键退出...")