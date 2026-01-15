"""
高级计算器工具
支持复杂数学运算、单位转换、统计分析
"""
import math
import statistics
import re
from typing import Dict, Any, List, Union
from decimal import Decimal, getcontext
from . import BaseTool

class CalculatorTool(BaseTool):
    """高级计算器工具"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="""执行数学计算和统计分析。支持：
1. 基本运算: +, -, *, /, %, **, //
2. 数学函数: sin, cos, tan, log, exp, sqrt, abs, round
3. 统计分析: 平均值、中位数、标准差、方差
4. 单位转换: 长度、重量、温度、货币
5. 表达式示例: "2+3 * 4", "sqrt(16)", "mean([1,2,3,4,5])", "10km to m"
"""
        )
        
        # 设置高精度计算
        getcontext().prec = 28
        
        # 单位转换表
        self.units = {
            'length': {
                'm': 1, 'km': 1000, 'cm': 0.01, 'mm': 0.001,
                'inch': 0.0254, 'ft': 0.3048, 'mile': 1609.344
            },
            'weight': {
                'kg': 1, 'g': 0.001, 'mg': 0.000001,
                'lb': 0.453592, 'oz': 0.0283495
            },
            'temperature': {
                'c': 'celsius', 'f': 'fahrenheit', 'k': 'kelvin'
            }
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        expression = input_data.get("expression", "")
        
        if not expression or not isinstance(expression, str):
            return False
        
        # 安全检查
        dangerous_patterns = [
            r'import\s+', r'exec\s*\(', r'eval\s*\(', r'__.*__',
            r'open\s*\(', r'os\.', r'sys\.', r'subprocess\.'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return False
        
        return True
    
    def execute(self, expression: str) -> str:
        """执行计算"""
        try:
            # 预处理表达式
            expr = self._preprocess_expression(expression)
            
            # 检查是否是单位转换
            if 'to' in expr.lower():
                return self._convert_units(expr)
            
            # 检查是否是统计分析
            if expr.startswith('mean(') or expr.startswith('median(') or \
               expr.startswith('std(') or expr.startswith('var('):
                return self._statistical_analysis(expr)
            
            # 普通数学计算
            result = self._evaluate_math(expr)
            
            return f"计算结果: {result}"
            
        except ZeroDivisionError:
            return "错误：除数不能为零"
        except ValueError as e:
            return f"输入错误: {str(e)}"
        except Exception as e:
            return f"计算错误: {str(e)}"
    
    def _preprocess_expression(self, expr: str) -> str:
        """预处理表达式"""
        # 替换中文运算符
        expr = expr.replace('×', '*').replace('÷', '/').replace('^', '**')
        
        # 替换常见函数名
        expr = re.sub(r'sin\s*\(', 'math.sin(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'cos\s*\(', 'math.cos(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'tan\s*\(', 'math.tan(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'sqrt\s*\(', 'math.sqrt(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'log\s*\(', 'math.log10(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'ln\s*\(', 'math.log(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'exp\s*\(', 'math.exp(', expr, flags=re.IGNORECASE)
        expr = re.sub(r'abs\s*\(', 'abs(', expr, flags=re.IGNORECASE)
        
        return expr
    
    def _evaluate_math(self, expr: str) -> Union[int, float, Decimal]:
        """计算数学表达式"""
        # 安全的环境
        safe_dict = {
            '__builtins__': {},
            'math': math,
            'pi': math.pi,
            'e': math.e,
            'abs': abs,
            'round': round,
            'sum': sum,
            'min': min,
            'max': max,
            'Decimal': Decimal
        }
        
        # 添加数学函数
        for func_name in ['sin', 'cos', 'tan', 'sqrt', 'log', 'log10', 'exp']:
            if hasattr(math, func_name):
                safe_dict[func_name] = getattr(math, func_name)
        
        result = eval(expr, safe_dict)
        
        # 格式化结果
        if isinstance(result, float):
            if result.is_integer():
                result = int(result)
            else:
                # 保留6位小数
                result = round(result, 6)
        
        return result
    
    def _convert_units(self, expr: str) -> str:
        """单位转换"""
        try:
            # 解析表达式，如 "10km to m"
            parts = expr.lower().split('to')
            if len(parts) != 2:
                return "格式错误，请使用 '10km to m' 格式"
            
            from_part = parts[0].strip()
            to_unit = parts[1].strip()
            
            # 提取数值和单位
            match = re.match(r'([\d\.]+)\s*([a-zA-Z]+)', from_part)
            if not match:
                return "无法解析数值和单位"
            
            value = float(match.group(1))
            from_unit = match.group(2)
            
            # 温度转换特殊处理
            if from_unit in ['c', 'f', 'k'] and to_unit in ['c', 'f', 'k']:
                result = self._convert_temperature(value, from_unit, to_unit)
                return f"{value}{from_unit.upper()} = {result}{to_unit.upper()}"
            
            # 查找单位类型
            unit_type = None
            for category, units in self.units.items():
                if from_unit in units and to_unit in units:
                    unit_type = category
                    break
            
            if not unit_type:
                return f"不支持 {from_unit} 到 {to_unit} 的转换"
            
            # 进行转换
            base_value = value * self.units[unit_type][from_unit]
            result = base_value / self.units[unit_type][to_unit]
            
            return f"{value}{from_unit} = {result:.4f}{to_unit}"
            
        except Exception as e:
            return f"单位转换错误: {str(e)}"
    
    def _convert_temperature(self, value: float, from_unit: str, to_unit: str) -> float:
        """温度转换"""
        # 先转到摄氏度
        if from_unit == 'c':
            celsius = value
        elif from_unit == 'f':
            celsius = (value - 32) * 5/9
        elif from_unit == 'k':
            celsius = value - 273.15
        else:
            raise ValueError(f"不支持的温度单位: {from_unit}")
        
        # 从摄氏度转到目标单位
        if to_unit == 'c':
            return celsius
        elif to_unit == 'f':
            return celsius * 9/5 + 32
        elif to_unit == 'k':
            return celsius + 273.15
        else:
            raise ValueError(f"不支持的温度单位: {to_unit}")
    
    def _statistical_analysis(self, expr: str) -> str:
        """统计分析"""
        try:
            # 提取数据
            match = re.search(r'\(\[([\d\.,\s]+)\]\)', expr)
            if not match:
                return "格式错误，请使用 'mean([1,2,3,4,5])' 格式"
            
            data_str = match.group(1)
            data = [float(x.strip()) for x in data_str.split(',')]
            
            if expr.startswith('mean('):
                result = statistics.mean(data)
                operation = "平均值"
            elif expr.startswith('median('):
                result = statistics.median(data)
                operation = "中位数"
            elif expr.startswith('std('):
                result = statistics.stdev(data)
                operation = "标准差"
            elif expr.startswith('var('):
                result = statistics.variance(data)
                operation = "方差"
            else:
                return "不支持的统计函数"
            
            return f"{operation}: {result:.4f} (数据: {data})"
            
        except Exception as e:
            return f"统计分析错误: {str(e)}"

# 创建工具实例
calculator_tool = CalculatorTool()