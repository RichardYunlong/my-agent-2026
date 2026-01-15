"""
网页工具
支持网页内容提取、API调用、数据抓取
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, Any, List, Optional
import json
from . import BaseTool

class WebTool(BaseTool):
    """网页工具"""
    
    def __init__(self):
        super().__init__(
            name="web_tool",
            description="""网页相关操作工具。支持：
1. 获取网页内容: 抓取网页文本内容
2. 提取链接: 提取网页中所有链接
3. 提取图片: 提取网页中所有图片
4. 调用API: 调用RESTful API接口
5. 解析JSON: 解析JSON格式数据
6. 示例: "获取https://example.com内容", "提取页面链接", "调用API获取数据"
"""
        )
        
        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # 超时设置
        self.timeout = 10
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        operation = input_data.get("operation", "")
        url = input_data.get("url", "")
        
        if not operation or not isinstance(operation, str):
            return False
        
        # 安全检查
        if url:
            # 检查URL格式
            if not url.startswith(('http://', 'https://')):
                return False
            
            # 检查危险域名
            dangerous_domains = ['localhost', '127.0.0.1', '192.168.', '10.']
            if any(domain in url for domain in dangerous_domains):
                return False
        
        return True
    
    def execute(self, operation: str, url: str = "", **kwargs) -> str:
        """执行网页操作"""
        try:
            operation = operation.lower().strip()
            
            if operation in ["fetch", "获取", "抓取"]:
                return self._fetch_webpage(url)
            
            elif operation in ["links", "链接", "提取链接"]:
                return self._extract_links(url)
            
            elif operation in ["images", "图片", "提取图片"]:
                return self._extract_images(url)
            
            elif operation in ["api", "调用api"]:
                method = kwargs.get("method", "GET")
                data = kwargs.get("data", {})
                return self._call_api(url, method, data)
            
            elif operation in ["parse_json", "解析json"]:
                json_str = kwargs.get("json_str", "")
                return self._parse_json(json_str)
            
            elif operation in ["help", "帮助"]:
                return self._get_help()
            
            else:
                return f"不支持的操作: {operation}\n{self._get_help()}"
                
        except Exception as e:
            return f"网页操作错误: {str(e)}"
    
    def _fetch_webpage(self, url: str) -> str:
        """获取网页内容"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                verify=True  # 验证SSL证书
            )
            
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 获取文本
            text = soup.get_text()
            
            # 清理文本
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # 限制长度
            if len(text) > 2000:
                text = text[:2000] + "\n...(内容截断，只显示前2000字符)"
            
            # 获取页面信息
            title = soup.title.string if soup.title else "无标题"
            
            result = [
                f"🌐 网页: {url}",
                f"📄 标题: {title}",
                f"📊 状态: {response.status_code}",
                f"📏 长度: {len(response.text)} 字符",
                f"\n📝 内容摘要:\n{text}"
            ]
            
            return "\n".join(result)
            
        except requests.exceptions.Timeout:
            return f"请求超时: {url}"
        except requests.exceptions.HTTPError as e:
            return f"HTTP错误: {e.response.status_code} - {url}"
        except requests.exceptions.ConnectionError:
            return f"连接错误: {url}"
        except requests.exceptions.RequestException as e:
            return f"请求错误: {str(e)}"
        except Exception as e:
            return f"解析错误: {str(e)}"
    
    def _extract_links(self, url: str) -> str:
        """提取链接"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有链接
            links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # 处理相对链接
                if href.startswith('/'):
                    href = requests.compat.urljoin(url, href)
                elif not href.startswith(('http://', 'https://')):
                    continue
                
                if text:
                    links.append(f"{text}: {href}")
                else:
                    links.append(f"{href}")
            
            if not links:
                return "未找到链接"
            
            result = [f"在 {url} 中找到 {len(links)} 个链接:"]
            for i, link in enumerate(links[:10], 1):
                result.append(f"{i}. {link}")
            
            if len(links) > 10:
                result.append(f"... 还有 {len(links) - 10} 个链接未显示")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"提取链接失败: {str(e)}"
    
    def _extract_images(self, url: str) -> str:
        """提取图片"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取所有图片
            images = []
            for img in soup.find_all('img', src=True):
                src = img.get('src')
                alt = img.get('alt', '无描述')
                
                # 处理相对路径
                if src.startswith('/'):
                    src = requests.compat.urljoin(url, src)
                elif not src.startswith(('http://', 'https://', 'data:image')):
                    continue
                
                images.append(f"{alt}: {src}")
            
            if not images:
                return "未找到图片"
            
            result = [f"在 {url} 中找到 {len(images)} 张图片:"]
            for i, img in enumerate(images[:5], 1):
                result.append(f"{i}. {img}")
            
            if len(images) > 5:
                result.append(f"... 还有 {len(images) - 5} 张图片未显示")
            
            return "\n".join(result)
            
        except Exception as e:
            return f"提取图片失败: {str(e)}"
    
    def _call_api(self, url: str, method: str = "GET", data: Dict = None) -> str:
        """调用API"""
        try:
            method = method.upper()
            
            if method == "GET":
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    json=data,
                    headers=self.headers,
                    timeout=self.timeout
                )
            elif method == "PUT":
                response = requests.put(
                    url,
                    json=data,
                    headers=self.headers,
                    timeout=self.timeout
                )
            elif method == "DELETE":
                response = requests.delete(
                    url,
                    headers=self.headers,
                    timeout=self.timeout
                )
            else:
                return f"不支持的HTTP方法: {method}"
            
            response.raise_for_status()
            
            # 解析响应
            try:
                json_data = response.json()
                formatted = json.dumps(json_data, ensure_ascii=False, indent=2)
                
                # 限制长度
                if len(formatted) > 2000:
                    formatted = formatted[:2000] + "\n...(JSON截断)"
                
                result = [
                    f"🌐 API: {url}",
                    f"📤 方法: {method}",
                    f"📊 状态: {response.status_code}",
                    f"\n📄 响应:\n{formatted}"
                ]
                
                return "\n".join(result)
                
            except ValueError:
                # 如果不是JSON，返回文本
                text = response.text[:1000]
                if len(response.text) > 1000:
                    text += "\n...(文本截断)"
                
                result = [
                    f"🌐 API: {url}",
                    f"📤 方法: {method}",
                    f"📊 状态: {response.status_code}",
                    f"\n📄 响应:\n{text}"
                ]
                
                return "\n".join(result)
            
        except requests.exceptions.RequestException as e:
            return f"API调用失败: {str(e)}"
        except Exception as e:
            return f"API处理失败: {str(e)}"
    
    def _parse_json(self, json_str: str) -> str:
        """解析JSON"""
        try:
            data = json.loads(json_str)
            
            # 格式化
            formatted = json.dumps(data, ensure_ascii=False, indent=2)
            
            # 限制长度
            if len(formatted) > 2000:
                formatted = formatted[:2000] + "\n...(JSON截断)"
            
            # 统计信息
            stats = self._analyze_json(data)
            
            result = [
                "📄 JSON解析结果:",
                f"📊 统计: {stats}",
                f"\n🔍 内容:\n{formatted}"
            ]
            
            return "\n".join(result)
            
        except json.JSONDecodeError as e:
            return f"JSON解析错误: {str(e)}"
        except Exception as e:
            return f"JSON处理失败: {str(e)}"
    
    def _analyze_json(self, data: Any) -> str:
        """分析JSON结构"""
        if isinstance(data, dict):
            count = len(data)
            types = {}
            for key, value in data.items():
                t = type(value).__name__
                types[t] = types.get(t, 0) + 1
            
            type_str = ", ".join([f"{k}:{v}" for k, v in types.items()])
            return f"对象 ({count}个键), 类型: {type_str}"
        
        elif isinstance(data, list):
            count = len(data)
            if count > 0:
                sample = data[0]
                return f"数组 ({count}个元素), 示例类型: {type(sample).__name__}"
            else:
                return f"空数组"
        
        else:
            return f"值类型: {type(data).__name__}"
    
    def _get_help(self) -> str:
        """获取帮助"""
        help_text = """
可用操作:
1. 获取网页: operation="fetch", url="https://example.com"
2. 提取链接: operation="links", url="https://example.com"
3. 提取图片: operation="images", url="https://example.com"
4. 调用API: operation="api", url="https://api.example.com", method="GET", data={{}} (可选)
5. 解析JSON: operation="parse_json", json_str='{{"key": "value"}}'

示例:
- 获取网页: operation="fetch", url="https://example.com"
- 调用API: operation="api", url="https://api.example.com/data", method="GET"
- 解析JSON: operation="parse_json", json_str='{{"name": "test"}}'
"""
        return help_text

# 创建工具实例
web_tool = WebTool()