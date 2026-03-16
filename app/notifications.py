from __future__ import annotations

import os
import subprocess
from plyer import notification
import winsound

from .config import NOTIFICATION_MESSAGES, NOTIFICATION_TITLE, SOUND_COMPLETE, SOUND_START
from .models import MonitoredFile


def _play_sound(path: str) -> None:
    try:
        if path and os.path.exists(path):
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        else:
            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception as e:  # pragma: no cover - 시스템 의존
        print(f"알림음 재생 실패: {e}")


def _notify_toast(title: str, body: str) -> None:
    try:
        notification.notify(title=title, message=body, timeout=5)
        return
    except Exception as e:  # pragma: no cover - plyer 실패 시
        print(f"알림 실패: {e}")

    # plyer 실패 시 PowerShell 토스트로 폴백
    try:
        subprocess.run(
            [
                "powershell",
                "-Command",
                (
                    "[Windows.UI.Notifications.ToastNotificationManager, "
                    "Windows.UI.Notifications, ContentType = WindowsRuntime];"
                    "$template = "
                    "[Windows.UI.Notifications.ToastNotificationManager]"
                    "::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]"
                    "::ToastText02);"
                    "$template.GetElementsByTagName('text').Item(0).AppendChild("
                    f"$template.CreateTextNode('{title}')) | Out-Null;"
                    "$template.GetElementsByTagName('text').Item(1).AppendChild("
                    f"$template.CreateTextNode('{body}')) | Out-Null;"
                    "$toast = [Windows.UI.Notifications.ToastNotification]::new($template);"
                    "[Windows.UI.Notifications.ToastNotificationManager]"
                    "::CreateToastNotifier('MXF Monitor').Show($toast);"
                ),
            ],
            shell=True,
        )
    except Exception as e2:  # pragma: no cover
        print(f"대체 알림도 실패: {e2}")


def notify_started(file: MonitoredFile) -> None:
    msg = NOTIFICATION_MESSAGES["started"]
    body = f"{file.name}\n{msg}"
    _notify_toast(NOTIFICATION_TITLE, body)
    _play_sound(SOUND_START)


def notify_completed(file: MonitoredFile) -> None:
    msg = NOTIFICATION_MESSAGES["completed"]
    body = f"{file.name}\n{msg}"
    _notify_toast(NOTIFICATION_TITLE, body)
    _play_sound(SOUND_COMPLETE)

