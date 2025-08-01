# utils/language_detector.py

import logging
import re

logger = logging.getLogger(__name__)


def detect_language(text: str) -> str:
    """
    检测文本的主要语言。
    如果文本中包含印地文字符，则认为是印地语 ('hi')。
    否则，默认为是英语 ('en')。
    """
    try:
        # 使用梵文Unicode范围来查找印地文字符
        hindi_chars = re.findall(r'[\u0900-\u097F]', text)

        if len(hindi_chars) > 0:
            logger.info("检测到印地文字符，语言设置为 'hi'。")
            return 'hi'
        else:
            logger.info("未检测到印地文字符，语言设置为 'en'。")
            return 'en'

    except Exception as e:
        logger.error(f"语言检测时发生未知错误: {e}")
        return 'en'  # 出现异常时，安全地默认为英语
