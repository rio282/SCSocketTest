import os
from winotify import Notification, audio, Notifier
from typing import Callable

from main import app_id


class Windows:
    def __init__(self):
        self.compatible = os.name == "nt"

    def notification(self, title: str, description: str, run_method_on_click: Callable, *method_params) -> None:
        if not self.compatible:
            return

        toast = Notification(
            app_id=app_id,
            title=title,
            msg=description
        )
        toast.set_audio(audio.Reminder, loop=False)
        # TODO: fix later
        # method = Notifier.register_callback(run_method_on_click, method_params)
        # toast.add_actions(label="Open", launch=method)

        toast.add_actions(label="Open", launch=method_params[0])
        toast.show()
