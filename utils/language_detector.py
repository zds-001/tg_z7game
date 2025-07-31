# utils/language_detector.py

import logging
import re

logger = logging.getLogger(__name__)


def is_indian_language(text: str) -> bool:
    """
    通过计算英文和印地文字符的占比来判断。
    如果英文和印地文字符总数占所有字母类字符的50%以上，则通过。
    """
    try:
        # 1. 找出所有英文字符 (a-z, A-Z)
        english_chars = re.findall(r'[a-zA-Z]', text)

        # 2. 找出所有印地文字符 (使用梵文Unicode范围)
        hindi_chars = re.findall(r'[\u0900-\u097F]', text)

        # 3. 计算目标语言（英文+印地文）的字符总数
        target_lang_char_count = len(english_chars) + len(hindi_chars)

        # 4. 计算所有“字母类”字符的总数 (忽略数字、空格、标点符号等)
        #    这是更科学的分母，而不是简单地用 len(text)
        total_letter_count = len([char for char in text if char.isalpha()])

        # 5. 避免除以零的错误
        if total_letter_count == 0:
            logger.info("文本不包含任何字母字符，默认通过。")
            return True

        # 6. 计算占比
        ratio = target_lang_char_count / total_letter_count

        logger.info(
            f"语言分析: 英文/印地文个数={target_lang_char_count}, "
            f"总字母个数={total_letter_count}, 占比={ratio:.2%}"
        )

        # 7. 判断占比是否大于等于50%
        if ratio >= 0.5:
            logger.info("占比超过50%，验证通过。")
            return True
        else:
            logger.warning("占比未超过50%，验证失败。")
            return False

    except Exception as e:
        logger.error(f"语言检测时发生未知错误: {e}")
        return False  # 出现异常时，默认为不通过
