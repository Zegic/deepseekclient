# File: app/config.py
# import datetime
import os
from datetime import datetime

# Application config
DEBUG = False
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev_key_change_in_production')
# Database config
DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'deepseek.db')
# DeepSeek API config
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-ffb9b568f769434d8c4b6b3e7a623d1b')
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-reasoner"
DEEPSEEK_TEMPERATURE = 1.2
SYSTEM_PROMPT = f"当前时间为:{datetime.now().strftime('%Y%m%d_%H%M%S')}作为参考。你的回答在大部分情况下应该使用汉语。在每个输出中，使用以下格式：\n\n**************************************\n\n{{content}}"
