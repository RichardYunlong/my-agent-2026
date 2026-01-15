"""
文件操作工具
支持文件读写、目录管理、文件信息查询
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
from . import BaseTool

class FileTool(BaseTool):
    """文件操作工具"""
    
    def __init__(self, base_path: str = "."):
        super().__init__(
            name="file_tool",
            description="""文件系统操作工具。支持：
1. 文件读取: 读取文本、JSON、CSV、Excel文件
2. 文件写入: 写入文本、JSON、CSV文件
3. 目录管理: 列出目录、创建目录、删除目录
4. 文件信息: 获取文件大小、修改时间、类型
5. 文件搜索: 按名称搜索文件
6. 示例: "读取data.txt", "列出当前目录", "创建目录test", "搜索*.py文件"
"""
        )
        
        # 设置基础路径
        self.base_path = Path(base_path).absolute()
        
        # 支持的文件类型
        self.supported_extensions = {
            '.txt': '文本文件',
            '.json': 'JSON文件',
            '.csv': 'CSV文件',
            '.xlsx': 'Excel文件',
            '.xls': 'Excel文件',
            '.py': 'Python文件',
            '.md': 'Markdown文件',
            '.log': '日志文件'
        }
        
        # 安全限制
        self.restricted_paths = [
            Path("/"),
            Path("/Windows"),
            Path("/System"),
            Path("/etc"),
            Path("/usr"),
            Path.home() / "Desktop",
            Path.home() / "Documents"
        ]
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        operation = input_data.get("operation", "")
        path = input_data.get("path", "")
        
        if not operation or not isinstance(operation, str):
            return False
        
        # 检查路径安全性
        if path:
            try:
                full_path = self._get_safe_path(path)
                if not self._is_path_safe(full_path):
                    return False
            except:
                return False
        
        return True
    
    def execute(self, operation: str, path: str = "", content: str = "", **kwargs) -> str:
        """执行文件操作"""
        try:
            operation = operation.lower().strip()
            
            if operation in ["read", "读取"]:
                return self._read_file(path)
            
            elif operation in ["write", "写入", "保存"]:
                return self._write_file(path, content)
            
            elif operation in ["list", "列出", "ls"]:
                return self._list_directory(path)
            
            elif operation in ["info", "信息", "详情"]:
                return self._get_file_info(path)
            
            elif operation in ["create_dir", "创建目录", "mkdir"]:
                return self._create_directory(path)
            
            elif operation in ["search", "搜索", "查找"]:
                pattern = kwargs.get("pattern", "*")
                return self._search_files(path, pattern)
            
            elif operation in ["exists", "存在", "检查"]:
                return self._check_exists(path)
            
            elif operation in ["help", "帮助"]:
                return self._get_help()
            
            else:
                return f"不支持的操作: {operation}\n{self._get_help()}"
                
        except Exception as e:
            return f"文件操作错误: {str(e)}"
    
    def _get_safe_path(self, path: str) -> Path:
        """获取安全路径"""
        if not path or path == ".":
            return self.base_path
        
        # 解析路径
        target_path = Path(path)
        
        # 如果是相对路径，转换为绝对路径
        if not target_path.is_absolute():
            target_path = self.base_path / target_path
        
        # 规范化路径
        target_path = target_path.resolve()
        
        # 确保路径在基础路径下
        try:
            target_path.relative_to(self.base_path)
        except ValueError:
            raise PermissionError(f"访问路径超出允许范围: {path}")
        
        return target_path
    
    def _is_path_safe(self, path: Path) -> bool:
        """检查路径是否安全"""
        # 检查是否在限制路径中
        for restricted in self.restricted_paths:
            try:
                path.relative_to(restricted)
                return False
            except ValueError:
                continue
        
        return True
    
    def _read_file(self, filepath: str) -> str:
        """读取文件"""
        try:
            full_path = self._get_safe_path(filepath)
            
            if not full_path.exists():
                return f"文件不存在: {filepath}"
            
            if not full_path.is_file():
                return f"不是文件: {filepath}"
            
            # 检查文件大小（限制10MB）
            if full_path.stat().st_size > 10 * 1024 * 1024:
                return f"文件过大（超过10MB）: {filepath}"
            
            # 根据扩展名选择读取方式
            ext = full_path.suffix.lower()
            
            if ext == '.json':
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return f"JSON内容:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
            
            elif ext == '.csv':
                with open(full_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                
                if not rows:
                    return "CSV文件为空"
                
                # 显示前5行
                preview = "\n".join([",".join(row) for row in rows[:5]])
                total = len(rows)
                return f"CSV内容 (前5行/共{total}行):\n{preview}"
            
            elif ext in ['.xlsx', '.xls']:
                try:
                    df = pd.read_excel(full_path, nrows=5)  # 只读前5行
                    return f"Excel内容 (前5行):\n{df.to_string()}"
                except:
                    return "无法读取Excel文件，可能需要安装openpyxl或xlrd"
            
            else:
                # 普通文本文件
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)  # 限制读取5000字符
                
                if len(content) == 5000:
                    content += "\n...(内容截断，只显示前5000字符)"
                
                return f"文件内容:\n{content}"
                
        except PermissionError:
            return f"没有权限读取文件: {filepath}"
        except Exception as e:
            return f"读取文件失败: {str(e)}"
    
    def _write_file(self, filepath: str, content: str) -> str:
        """写入文件"""
        try:
            full_path = self._get_safe_path(filepath)
            
            # 检查父目录是否存在
            parent = full_path.parent
            if not parent.exists():
                return f"父目录不存在: {parent}"
            
            # 写入文件
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return f"文件保存成功: {filepath}"
            
        except PermissionError:
            return f"没有权限写入文件: {filepath}"
        except Exception as e:
            return f"写入文件失败: {str(e)}"
    
    def _list_directory(self, dirpath: str) -> str:
        """列出目录"""
        try:
            if not dirpath:
                dirpath = "."
            
            full_path = self._get_safe_path(dirpath)
            
            if not full_path.exists():
                return f"目录不存在: {dirpath}"
            
            if not full_path.is_dir():
                return f"不是目录: {dirpath}"
            
            # 获取目录内容
            items = list(full_path.iterdir())
            
            if not items:
                return f"目录为空: {dirpath}"
            
            # 分类
            dirs = []
            files = []
            
            for item in items:
                if item.is_dir():
                    dirs.append(f"📁 {item.name}/")
                else:
                    # 显示文件大小
                    size = item.stat().st_size
                    size_str = self._format_size(size)
                    files.append(f"📄 {item.name} ({size_str})")
            
            # 构建结果
            result = [f"目录: {dirpath}"]
            
            if dirs:
                result.append("\n📁 目录:")
                result.extend(dirs[:10])  # 限制显示10个
            
            if files:
                result.append("\n📄 文件:")
                result.extend(files[:10])  # 限制显示10个
            
            total_count = len(dirs) + len(files)
            if total_count > 20:
                result.append(f"\n... 共 {total_count} 个项目，只显示前20个")
            
            return "\n".join(result)
            
        except PermissionError:
            return f"没有权限访问目录: {dirpath}"
        except Exception as e:
            return f"列出目录失败: {str(e)}"
    
    def _get_file_info(self, filepath: str) -> str:
        """获取文件信息"""
        try:
            full_path = self._get_safe_path(filepath)
            
            if not full_path.exists():
                return f"文件不存在: {filepath}"
            
            stat = full_path.stat()
            
            info = [
                f"📁 文件: {filepath}",
                f"📊 大小: {self._format_size(stat.st_size)}",
                f"📅 创建: {self._format_time(stat.st_ctime)}",
                f"✏️  修改: {self._format_time(stat.st_mtime)}",
                f"👀 访问: {self._format_time(stat.st_atime)}",
                f"🔢 模式: {oct(stat.st_mode)[-3:]}"
            ]
            
            if full_path.is_file():
                info.append(f"📄 类型: {self.supported_extensions.get(full_path.suffix.lower(), '未知文件')}")
            
            return "\n".join(info)
            
        except PermissionError:
            return f"没有权限访问文件: {filepath}"
        except Exception as e:
            return f"获取文件信息失败: {str(e)}"
    
    def _create_directory(self, dirpath: str) -> str:
        """创建目录"""
        try:
            full_path = self._get_safe_path(dirpath)
            
            if full_path.exists():
                return f"目录已存在: {dirpath}"
            
            full_path.mkdir(parents=True, exist_ok=True)
            return f"目录创建成功: {dirpath}"
            
        except PermissionError:
            return f"没有权限创建目录: {dirpath}"
        except Exception as e:
            return f"创建目录失败: {str(e)}"
    
    def _search_files(self, dirpath: str, pattern: str = "*") -> str:
        """搜索文件"""
        try:
            if not dirpath:
                dirpath = "."
            
            full_path = self._get_safe_path(dirpath)
            
            if not full_path.exists():
                return f"目录不存在: {dirpath}"
            
            if not full_path.is_dir():
                return f"不是目录: {dirpath}"
            
            # 搜索文件
            import fnmatch
            matches = []
            
            for root, dirs, files in os.walk(full_path):
                # 限制深度
                if root.count(os.sep) - str(full_path).count(os.sep) > 3:
                    continue
                
                for file in files:
                    if fnmatch.fnmatch(file, pattern):
                        matches.append(os.path.join(root, file))
                
                # 限制结果数量
                if len(matches) >= 20:
                    break
            
            if not matches:
                return f"在 {dirpath} 中未找到匹配 '{pattern}' 的文件"
            
            result = [f"在 {dirpath} 中找到 {len(matches)} 个匹配 '{pattern}' 的文件:"]
            for i, match in enumerate(matches[:10], 1):
                rel_path = os.path.relpath(match, full_path)
                result.append(f"{i}. {rel_path}")
            
            if len(matches) > 10:
                result.append(f"... 还有 {len(matches) - 10} 个文件未显示")
            
            return "\n".join(result)
            
        except PermissionError:
            return f"没有权限搜索目录: {dirpath}"
        except Exception as e:
            return f"搜索文件失败: {str(e)}"
    
    def _check_exists(self, path: str) -> str:
        """检查文件/目录是否存在"""
        try:
            full_path = self._get_safe_path(path)
            
            if full_path.exists():
                if full_path.is_file():
                    return f"文件存在: {path}"
                else:
                    return f"目录存在: {path}"
            else:
                return f"不存在: {path}"
            
        except Exception as e:
            return f"检查失败: {str(e)}"
    
    def _get_help(self) -> str:
        """获取帮助"""
        help_text = """
可用操作:
1. 读取文件: operation="read", path="文件名"
2. 写入文件: operation="write", path="文件名", content="内容"
3. 列出目录: operation="list", path="目录路径" (可选)
4. 文件信息: operation="info", path="文件路径"
5. 创建目录: operation="create_dir", path="目录路径"
6. 搜索文件: operation="search", path="目录路径", pattern="*.py"
7. 检查存在: operation="exists", path="路径"

示例:
- 读取data.txt: operation="read", path="data.txt"
- 列出当前目录: operation="list"
- 创建test目录: operation="create_dir", path="test"
"""
        return help_text
    
    def _format_size(self, size_bytes: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def _format_time(self, timestamp: float) -> str:
        """格式化时间"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime('%Y-%m-%d %H:%M:%S')

# 创建工具实例
file_tool = FileTool()