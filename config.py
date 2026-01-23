from dotenv import load_dotenv
import os

load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")

# 安全获取 PORT 环境变量，处理空值/非数字情况
def get_port():
    try:
        port_str = os.getenv("PORT")
        # 如果 PORT 为空字符串/None，或无法转整数，返回默认值
        if not port_str:
            return 8000
        return int(port_str)
    except (ValueError, TypeError):
        return 8000

PORT = get_port()

# 自定义配置
MAX_HISTORY = 8  # 最多保留8轮对话历史
MAX_MEMORY_LEN = 500  # 用户记忆最大长度
SENSITIVE_WORDS = ["自杀", "自残", "暴力", "色情"]
STREAM_DELAY = 0.05  # 流式输出字间隔（秒）

# 关键：新增进度存储全局字典（修复导入错误的核心）
customize_progress = {}


