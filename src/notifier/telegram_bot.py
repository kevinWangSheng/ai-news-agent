"""
Telegram Bot 通知器
负责将日报发送到Telegram
"""

import os
import requests
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram通知器"""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    def send_message(
        self,
        message: str,
        parse_mode: str = "Markdown",
        disable_preview: bool = True
    ) -> bool:
        """
        发送消息到Telegram

        Args:
            message: 消息内容（支持Markdown）
            parse_mode: 解析模式 (Markdown/HTML)
            disable_preview: 是否禁用链接预览

        Returns:
            发送是否成功
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram bot_token or chat_id not configured")
            return False

        try:
            # Telegram消息长度限制为4096字符
            # 如果消息太长，分段发送
            if len(message) > 4000:
                return self._send_long_message(message, parse_mode, disable_preview)

            url = f"{self.base_url}/sendMessage"

            payload = {
                'chat_id': self.chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': disable_preview
            }

            response = requests.post(url, json=payload, timeout=10)

            if response.status_code == 200:
                logger.info("Message sent to Telegram successfully")
                return True
            else:
                logger.error(f"Telegram API error: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def _send_long_message(
        self,
        message: str,
        parse_mode: str,
        disable_preview: bool
    ) -> bool:
        """分段发送长消息"""
        chunks = self._split_message(message, max_length=4000)

        success = True
        for i, chunk in enumerate(chunks):
            logger.info(f"Sending message part {i+1}/{len(chunks)}")
            if not self.send_message(chunk, parse_mode, disable_preview):
                success = False

        return success

    def _split_message(self, message: str, max_length: int = 4000) -> list:
        """
        智能分割消息（按段落分割，保持Markdown格式完整）
        """
        if len(message) <= max_length:
            return [message]

        chunks = []
        lines = message.split('\n')
        current_chunk = ""

        for line in lines:
            if len(current_chunk) + len(line) + 1 <= max_length:
                current_chunk += line + '\n'
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = line + '\n'

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def send_daily_report(self, report: str) -> bool:
        """
        发送每日报告

        Args:
            report: Markdown格式的日报
        """
        # 添加时间戳和标题
        from datetime import datetime

        header = f"📅 *每日 AI Agent 技术博客精选*\n"
        header += f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header += "=" * 30 + "\n\n"

        full_report = header + report

        return self.send_message(full_report)

    def test_connection(self) -> bool:
        """测试Telegram连接"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                bot_info = response.json()
                bot_name = bot_info.get('result', {}).get('username', 'Unknown')
                logger.info(f"Telegram bot connected: @{bot_name}")
                return True
            else:
                logger.error(f"Telegram connection failed: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error testing Telegram connection: {e}")
            return False
