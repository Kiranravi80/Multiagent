"""Notification Manager.

Dispatches notices and alerts over email, Discord webhooks, and Telegram bots.
"""

from __future__ import annotations

import asyncio
from email.mime.text import MIMEText
import smtplib
from typing import Any
import httpx

from app.core.logging import get_logger

logger = get_logger(__name__)


class NotificationManager:
    """Consolidated dispatch manager for user alert channels."""

    def __init__(self, settings: Any) -> None:
        self._settings = settings

    async def send_discord(self, message: str) -> bool:
        """Post a text message to a Discord channel via webhook."""
        url = self._settings.discord_webhook_url
        if not url:
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={"content": message})
                response.raise_for_status()
                return True
        except Exception as exc:
            logger.error("discord_notification_failed", error=str(exc))
            return False

    async def send_telegram(self, message: str) -> bool:
        """Send a text message using a Telegram bot."""
        token = self._settings.telegram_bot_token
        chat_id = self._settings.telegram_chat_id
        if not token or not chat_id:
            return False

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json={"chat_id": chat_id, "text": message})
                response.raise_for_status()
                return True
        except Exception as exc:
            logger.error("telegram_notification_failed", error=str(exc))
            return False

    async def send_email(self, subject: str, body: str, to_email: str | None = None) -> bool:
        """Send an email using SMTP credentials."""
        host = self._settings.smtp_host
        port = self._settings.smtp_port
        user = self._settings.smtp_username
        password = self._settings.smtp_password
        from_email = self._settings.smtp_from_email
        dest = to_email or from_email

        if not host or not from_email:
            return False

        try:
            msg = MIMEText(body)
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = dest

            def _send() -> None:
                with smtplib.SMTP(host, port) as server:
                    if port == 587:
                        server.starttls()
                    if user and password:
                        server.login(user, password)
                    server.sendmail(from_email, [dest], msg.as_string())

            await asyncio.to_thread(_send)
            return True
        except Exception as exc:
            logger.error("smtp_email_failed", error=str(exc))
            return False

    async def notify(self, message: str, subject: str = "PAIOS Alert") -> None:
        """Asynchronously dispatch message to all configured endpoints."""
        logger.info("dispatching_notifications", message_preview=message[:60])
        tasks = []
        if self._settings.discord_webhook_url:
            tasks.append(self.send_discord(message))
        if self._settings.telegram_bot_token and self._settings.telegram_chat_id:
            tasks.append(self.send_telegram(message))
        if self._settings.smtp_host:
            tasks.append(self.send_email(subject, message))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
