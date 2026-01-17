from dotenv import load_dotenv
import os

load_dotenv()

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")

# 服务器配置
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# 自定义配置
MAX_HISTORY = 8  # 最多保留8轮对话历史
MAX_MEMORY_LEN = 500  # 用户记忆最大长度
SENSITIVE_WORDS = ["自杀", "自残", "暴力", "色情"]
STREAM_DELAY = 0.05  # 流式输出字间隔（秒）

# 关键：新增进度存储全局字典（修复导入错误的核心）
customize_progress = {}