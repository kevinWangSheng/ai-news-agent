"""
邮件通知器
负责将日报发送到邮箱
"""

import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Optional
import markdown

logger = logging.getLogger(__name__)


def _open_smtp(server: str, port: int) -> smtplib.SMTP:
    """端口 465 必须用 SMTP_SSL（隐式 TLS），其它端口用 SMTP + STARTTLS。"""
    if port == 465:
        return smtplib.SMTP_SSL(server, port, timeout=30)
    conn = smtplib.SMTP(server, port, timeout=30)
    conn.starttls()
    return conn


class EmailNotifier:
    """邮件通知器"""

    def __init__(
        self,
        sender_email: Optional[str] = None,
        sender_password: Optional[str] = None,
        receiver_email: Optional[str] = None,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None
    ):
        """
        初始化邮件通知器

        Args:
            sender_email: 发件人邮箱（默认从环境变量读取）
            sender_password: 发件人密码/App Password（默认从环境变量读取）
            receiver_email: 收件人邮箱（默认从环境变量读取）
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
        """
        self.sender_email = sender_email or os.getenv('EMAIL_SENDER')
        self.sender_password = sender_password or os.getenv('EMAIL_PASSWORD')
        self.receiver_email = receiver_email or os.getenv('EMAIL_RECEIVER')

        # 自动检测SMTP配置
        if smtp_server and smtp_port:
            self.smtp_server = smtp_server
            self.smtp_port = smtp_port
        else:
            # 根据邮箱类型自动配置
            self.smtp_server, self.smtp_port = self._detect_smtp_config(self.sender_email)

    def _detect_smtp_config(self, email: str) -> tuple:
        """根据邮箱地址自动检测SMTP配置"""
        if not email:
            return "smtp.gmail.com", 587

        email_lower = email.lower()

        if '@qq.com' in email_lower:
            return "smtp.qq.com", 465
        elif '@163.com' in email_lower:
            return "smtp.163.com", 465
        elif '@126.com' in email_lower:
            return "smtp.126.com", 465
        elif '@outlook.com' in email_lower or '@hotmail.com' in email_lower:
            return "smtp.office365.com", 587
        elif '@gmail.com' in email_lower:
            return "smtp.gmail.com", 587
        else:
            # 默认使用Gmail配置
            return "smtp.gmail.com", 587

    def send_message(
        self,
        subject: str,
        body: str,
        format_type: str = "markdown"
    ) -> bool:
        """
        发送邮件

        Args:
            subject: 邮件主题
            body: 邮件内容（支持Markdown或纯文本）
            format_type: 格式类型 (markdown/plain/html)

        Returns:
            发送是否成功
        """
        if not self.sender_email or not self.sender_password or not self.receiver_email:
            logger.error("Email configuration not complete")
            return False

        # 创建邮件对象
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = self.receiver_email

        # 添加纯文本版本
        text_content = self._markdown_to_plain_text(body) if format_type == "markdown" else body
        message.attach(MIMEText(text_content, "plain", "utf-8"))

        # 如果是Markdown，添加HTML版本
        if format_type == "markdown":
            message.attach(MIMEText(self._markdown_to_html(body), "html", "utf-8"))
        elif format_type == "html":
            message.attach(MIMEText(body, "html", "utf-8"))

        last_exc: Optional[Exception] = None
        for attempt in range(1, 4):
            try:
                with _open_smtp(self.smtp_server, self.smtp_port) as server:
                    server.login(self.sender_email, self.sender_password)
                    server.send_message(message)
                logger.info(f"Email sent successfully to {self.receiver_email}")
                return True
            except smtplib.SMTPAuthenticationError as e:
                # 认证失败重试也没意义，直接退出
                logger.error(
                    f"SMTP authentication failed via {self.smtp_server}:{self.smtp_port} — "
                    f"QQ 邮箱必须用授权码（不是登录密码），Gmail 必须用 App Password。{e}"
                )
                return False
            except Exception as e:
                last_exc = e
                logger.warning(
                    f"SMTP send attempt {attempt}/3 failed via "
                    f"{self.smtp_server}:{self.smtp_port}: {e}"
                )
                if attempt < 3:
                    time.sleep(2 ** attempt)  # 2s, 4s

        logger.error(
            f"Error sending email after 3 attempts via "
            f"{self.smtp_server}:{self.smtp_port}: {last_exc}"
        )
        return False

    def send_daily_report(self, report: str) -> bool:
        """
        发送每日报告

        Args:
            report: Markdown格式的日报
        """
        # 生成邮件主题
        date_str = datetime.now().strftime('%Y-%m-%d')
        subject = f"每日 AI Agent 技术博客精选 - {date_str}"

        # 添加邮件头部
        header = f"""
# 每日 AI Agent 技术博客精选
{datetime.now().strftime('%Y-%m-%d %H:%M')}

---

"""
        full_report = header + report

        # 添加邮件底部
        footer = f"""

---
由AI自动聚合并筛选 | 专注AI Agent领域
"""
        full_report += footer

        return self.send_message(subject, full_report, format_type="markdown")

    def _markdown_to_html(self, markdown_text: str) -> str:
        """将Markdown转换为HTML"""
        try:
            # 使用markdown库转换
            html = markdown.markdown(
                markdown_text,
                extensions=['extra', 'codehilite', 'tables', 'nl2br']
            )

            # 添加CSS样式
            styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f6f8fa;
        }}
        h1, h2, h3 {{
            color: #24292e;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        h1 {{ font-size: 2em; }}
        h2 {{ font-size: 1.5em; margin-top: 24px; }}
        h3 {{ font-size: 1.25em; }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul {{
            padding-left: 2em;
        }}
        li {{
            margin-bottom: 0.5em;
        }}
        code {{
            background-color: #f6f8fa;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
            font-size: 85%;
        }}
        pre {{
            background-color: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow: auto;
        }}
        blockquote {{
            border-left: 4px solid #dfe2e5;
            padding-left: 16px;
            color: #6a737d;
            margin-left: 0;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #eaecef;
            margin: 24px 0;
        }}
        .content {{
            background-color: white;
            padding: 30px;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }}
    </style>
</head>
<body>
    <div class="content">
        {html}
    </div>
</body>
</html>
"""
            return styled_html

        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {e}")
            # 降级：简单的换行转<br>
            return markdown_text.replace('\n', '<br>')

    def _markdown_to_plain_text(self, markdown_text: str) -> str:
        """将Markdown转换为纯文本（移除Markdown语法）"""
        import re

        text = markdown_text

        # 移除链接但保留文字 [text](url) -> text (url)
        text = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\1 (\2)', text)

        # 移除图片
        text = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', r'\1', text)

        # 移除粗体和斜体标记
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'_([^_]+)_', r'\1', text)

        # 移除代码块标记
        text = re.sub(r'`([^`]+)`', r'\1', text)

        # 移除标题标记
        text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)

        return text

    def test_connection(self) -> bool:
        """测试邮件服务器连接"""
        if not self.sender_email or not self.sender_password:
            logger.error("Email sender not configured")
            return False

        try:
            with _open_smtp(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)

            logger.info(f"Email server connection successful: {self.smtp_server}:{self.smtp_port}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed")
            logger.error("For Gmail: Make sure you're using an App Password")
            logger.error("Visit: https://myaccount.google.com/apppasswords")
            return False
        except Exception as e:
            logger.error(f"Email connection test failed via {self.smtp_server}:{self.smtp_port}: {e}")
            return False

    def send_test_email(self) -> bool:
        """发送测试邮件"""
        test_subject = "🧪 新闻聚合系统测试邮件"
        test_body = """
# 测试邮件

这是来自**新闻聚合系统**的测试邮件。

如果你看到这封邮件，说明配置成功！

## 功能特点

- ✅ 自动搜集全球科技资讯
- ✅ AI智能筛选高质量内容
- ✅ 每日定时推送到邮箱

---

**系统配置正常，即将开始发送日报。**
"""

        return self.send_message(test_subject, test_body, format_type="markdown")
