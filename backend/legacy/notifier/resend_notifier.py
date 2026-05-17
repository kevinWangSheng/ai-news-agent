"""
Resend 邮件通知器（HTTP API，不走 SMTP）
用于绕开 GitHub Actions 出口 IP 在 SMTP 服务商上的反滥用拦截。
"""

import os
import time
import logging
from typing import Optional

import requests

from .email_notifier import EmailNotifier

logger = logging.getLogger(__name__)

RESEND_ENDPOINT = "https://api.resend.com/emails"
DEFAULT_FROM = "AI Agent News <onboarding@resend.dev>"


class ResendNotifier(EmailNotifier):
    """复用 EmailNotifier 的 markdown→html / send_daily_report 逻辑，把 SMTP 替换为 Resend HTTP API。"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        sender_from: Optional[str] = None,
        receiver_email: Optional[str] = None,
    ):
        # 父类 init 会做 SMTP 探测；我们不需要 SMTP，所以跳过 super().__init__()
        self.api_key = api_key or os.getenv("RESEND_API_KEY")
        self.sender_from = sender_from or os.getenv("RESEND_FROM") or DEFAULT_FROM
        self.receiver_email = receiver_email or os.getenv("EMAIL_RECEIVER")

        # EmailNotifier.send_daily_report 引用了 self.sender_email；这里用 from 字段兜底
        self.sender_email = self.sender_from
        self.sender_password = None
        self.smtp_server = "resend-http"
        self.smtp_port = 0

    def send_message(self, subject: str, body: str, format_type: str = "markdown") -> bool:
        if not self.api_key:
            logger.error("Resend not configured: RESEND_API_KEY missing")
            return False
        if not self.receiver_email:
            logger.error("Resend not configured: EMAIL_RECEIVER missing")
            return False

        text_content = self._markdown_to_plain_text(body) if format_type == "markdown" else body
        if format_type == "markdown":
            html_content = self._markdown_to_html(body)
        elif format_type == "html":
            html_content = body
        else:
            html_content = f"<pre>{body}</pre>"

        payload = {
            "from": self.sender_from,
            "to": self.receiver_email,
            "subject": subject,
            "html": html_content,
            "text": text_content,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        last_err: Optional[str] = None
        for attempt in range(1, 4):
            try:
                resp = requests.post(RESEND_ENDPOINT, json=payload, headers=headers, timeout=20)
                if resp.status_code == 200:
                    msg_id = resp.json().get("id", "?")
                    logger.info(f"Resend email sent to {self.receiver_email} (id={msg_id})")
                    return True
                # 401/403 不必重试
                if resp.status_code in (401, 403):
                    logger.error(
                        f"Resend rejected request (HTTP {resp.status_code}): {resp.text[:300]}"
                    )
                    return False
                last_err = f"HTTP {resp.status_code} {resp.text[:200]}"
                logger.warning(f"Resend send attempt {attempt}/3 failed: {last_err}")
            except Exception as e:
                last_err = str(e)
                logger.warning(f"Resend send attempt {attempt}/3 errored: {e}")

            if attempt < 3:
                time.sleep(2 ** attempt)  # 2s, 4s

        logger.error(f"Resend email failed after 3 attempts: {last_err}")
        return False

    def test_connection(self) -> bool:
        if not self.api_key:
            logger.error("Resend API key not configured")
            return False
        try:
            # Resend 没有 ping 接口；用 GET /domains 做轻量鉴权探测
            resp = requests.get(
                "https://api.resend.com/domains",
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=10,
            )
            if resp.status_code in (200, 401, 403):
                ok = resp.status_code == 200
                logger.info(f"Resend auth check: HTTP {resp.status_code} ({'OK' if ok else 'unauthorized'})")
                return ok
            logger.error(f"Resend connection test unexpected status: {resp.status_code}")
            return False
        except Exception as e:
            logger.error(f"Resend connection test error: {e}")
            return False
