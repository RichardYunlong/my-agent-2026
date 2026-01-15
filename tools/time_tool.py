"""
时间工具
支持时间查询、日期计算、时区转换、倒计时
"""
from datetime import datetime, timedelta, date
import pytz
from typing import Dict, Any, List, Optional
from . import BaseTool

class TimeTool(BaseTool):
    """时间工具"""
    
    def __init__(self):
        super().__init__(
            name="time_tool",
            description="""获取和处理时间信息。支持：
1. 当前时间: 查询本地时间、UTC时间、指定时区时间
2. 日期计算: 计算未来/过去日期、日期差、工作日计算
3. 时间格式: 多种格式显示时间
4. 时区转换: 全球主要时区转换
5. 示例: "现在时间", "UTC时间", "北京时间", "3天后", "2024-01-01到2024-12-31的天数"
"""
        )
        
        # 常用时区
        self.timezones = {
            '北京': 'Asia/Shanghai',
            '上海': 'Asia/Shanghai',
            '广州': 'Asia/Shanghai',
            '深圳': 'Asia/Shanghai',
            '纽约': 'America/New_York',
            '伦敦': 'Europe/London',
            '东京': 'Asia/Tokyo',
            '巴黎': 'Europe/Paris',
            '悉尼': 'Australia/Sydney',
            'UTC': 'UTC'
        }
    
    def execute(self, query: str) -> str:
        """处理时间查询"""
        query = query.lower().strip()
        
        try:
            if query in ["现在", "当前时间", "现在几点了", "时间"]:
                return self._get_current_time()
            
            elif "utc" in query:
                return self._get_utc_time()
            
            elif "时区" in query or "timezone" in query:
                return self._handle_timezone_query(query)
            
            elif "天后" in query or "days after" in query:
                return self._calculate_future_date(query)
            
            elif "天前" in query or "days ago" in query:
                return self._calculate_past_date(query)
            
            elif "相差" in query or "difference" in query or "到" in query:
                return self._calculate_date_difference(query)
            
            elif "星期" in query or "周" in query:
                return self._get_weekday_info(query)
            
            elif "农历" in query or "阴历" in query:
                return self._get_chinese_calendar()
            
            elif "倒计时" in query or "countdown" in query:
                return self._countdown_to_date(query)
            
            else:
                # 默认返回详细信息
                return self._get_detailed_time_info()
                
        except Exception as e:
            return f"时间查询错误: {str(e)}"
    
    def _get_current_time(self) -> str:
        """获取当前时间"""
        now = datetime.now()
        return self._format_time_detail(now, "本地时间")
    
    def _get_utc_time(self) -> str:
        """获取UTC时间"""
        utc_now = datetime.utcnow()
        return self._format_time_detail(utc_now, "UTC时间")
    
    def _handle_timezone_query(self, query: str) -> str:
        """处理时区查询"""
        # 提取时区名称
        for tz_name, tz_id in self.timezones.items():
            if tz_name in query:
                try:
                    tz = pytz.timezone(tz_id)
                    tz_time = datetime.now(tz)
                    return self._format_time_detail(tz_time, f"{tz_name}时间")
                except:
                    return f"无法获取 {tz_name} 时区时间"
        
        return f"支持时区: {', '.join(self.timezones.keys())}"
    
    def _calculate_future_date(self, query: str) -> str:
        """计算未来日期"""
        try:
            # 提取天数
            import re
            match = re.search(r'(\d+)\s*天后', query)
            if not match:
                match = re.search(r'(\d+)\s*days\s*after', query, re.IGNORECASE)
            
            if match:
                days = int(match.group(1))
                future_date = datetime.now() + timedelta(days=days)
                weekday = self._get_chinese_weekday(future_date.weekday())
                return f"{days}天后是: {future_date.strftime('%Y年%m月%d日')} {weekday}"
        except:
            pass
        
        return "格式错误，请使用 '3天后' 格式"
    
    def _calculate_past_date(self, query: str) -> str:
        """计算过去日期"""
        try:
            import re
            match = re.search(r'(\d+)\s*天前', query)
            if not match:
                match = re.search(r'(\d+)\s*days\s*ago', query, re.IGNORECASE)
            
            if match:
                days = int(match.group(1))
                past_date = datetime.now() - timedelta(days=days)
                weekday = self._get_chinese_weekday(past_date.weekday())
                return f"{days}天前是: {past_date.strftime('%Y年%m月%d日')} {weekday}"
        except:
            pass
        
        return "格式错误，请使用 '3天前' 格式"
    
    def _calculate_date_difference(self, query: str) -> str:
        """计算日期差"""
        try:
            import re
            # 提取两个日期
            dates = re.findall(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', query)
            if len(dates) == 2:
                date1 = datetime.strptime(dates[0].replace('/', '-'), '%Y-%m-%d')
                date2 = datetime.strptime(dates[1].replace('/', '-'), '%Y-%m-%d')
                
                diff = abs((date2 - date1).days)
                return f"{dates[0]} 和 {dates[1]} 相差 {diff} 天"
        except:
            pass
        
        return "格式错误，请使用 '2024-01-01到2024-12-31的天数' 格式"
    
    def _get_weekday_info(self, query: str) -> str:
        """获取星期信息"""
        now = datetime.now()
        weekday = self._get_chinese_weekday(now.weekday())
        
        if "今天" in query:
            return f"今天是{now.strftime('%Y年%m月%d日')}，{weekday}"
        elif "明天" in query:
            tomorrow = now + timedelta(days=1)
            tomorrow_weekday = self._get_chinese_weekday(tomorrow.weekday())
            return f"明天是{tomorrow.strftime('%Y年%m月%d日')}，{tomorrow_weekday}"
        elif "昨天" in query:
            yesterday = now - timedelta(days=1)
            yesterday_weekday = self._get_chinese_weekday(yesterday.weekday())
            return f"昨天是{yesterday.strftime('%Y年%m月%d日')}，{yesterday_weekday}"
        else:
            return f"今天是{now.strftime('%Y年%m月%d日')}，{weekday}"
    
    def _get_chinese_calendar(self) -> str:
        """获取农历信息（简化版）"""
        now = datetime.now()
        # 这里可以集成真正的农历计算库
        return f"当前日期: {now.strftime('%Y年%m月%d日')}\n注：完整的农历功能需要安装lunarcalendar库"
    
    def _countdown_to_date(self, query: str) -> str:
        """倒计时"""
        try:
            import re
            # 提取目标日期
            match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', query)
            if match:
                target_date = datetime.strptime(match.group(1).replace('/', '-'), '%Y-%m-%d')
                today = datetime.now()
                
                if target_date < today:
                    diff = (today - target_date).days
                    return f"{match.group(1)} 已经过去 {diff} 天了"
                else:
                    diff = (target_date - today).days
                    return f"距离 {match.group(1)} 还有 {diff} 天"
        except:
            pass
        
        return "格式错误，请使用 '倒计时到2024-12-31' 格式"
    
    def _get_detailed_time_info(self) -> str:
        """获取详细信息"""
        now = datetime.now()
        weekday = self._get_chinese_weekday(now.weekday())
        
        info = [
            f"📅 日期: {now.strftime('%Y年%m月%d日')}",
            f"⏰ 时间: {now.strftime('%H:%M:%S')}",
            f"📆 星期: {weekday}",
            f"🔄 时间戳: {int(now.timestamp())}",
            f"🌍 时区: 中国标准时间 (UTC+8)"
        ]
        
        return "\n".join(info)
    
    def _format_time_detail(self, dt: datetime, label: str) -> str:
        """格式化时间详情"""
        weekday = self._get_chinese_weekday(dt.weekday())
        return f"{label}:\n  📅 {dt.strftime('%Y-%m-%d')}\n  ⏰ {dt.strftime('%H:%M:%S')}\n  📆 {weekday}"
    
    def _get_chinese_weekday(self, weekday_num: int) -> str:
        """获取中文星期"""
        weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        return weekdays[weekday_num]

# 创建工具实例
time_tool = TimeTool()