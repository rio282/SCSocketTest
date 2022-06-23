import os
from pathlib import Path
from typing import Callable, Final
from winotify import Notification, audio, Notifier


class Windows:
    def __init__(self):
        self.compatible = os.name == "nt"
        self.app_id: Final[str] = f"PID::{os.getpid()}"

    def notification(self, title: str, description: str, run_method_on_click: Callable, *method_params) -> None:
        if not self.compatible:
            return

        toast = Notification(
            app_id=self.app_id,
            title=title,
            msg=description
        )
        toast.set_audio(audio.Reminder, loop=False)
        # TODO: fix later
        # method = Notifier.register_callback(run_method_on_click, method_params)
        # toast.add_actions(label="Open", launch=method)

        toast.add_actions(label="Open", launch=method_params[0])
        toast.show()

    @staticmethod
    def get_downloads_folder() -> str:
        return str(Path.home() / "Downloads")
