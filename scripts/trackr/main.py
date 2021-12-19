import time
import os
import json
import sys
import datetime

import psutil
import prettytable

from typing import Optional, Tuple, List, Dict
from plyer import notification
from gi.repository import Gtk, Wnck

RGB_RED = (255, 0, 0)
RGB_YELLOW = (237, 255, 48)
RGB_GREEN = (0, 255, 25)


def __colored(text: str, colors: Tuple[int, int, int]) -> str:
    """Return colored string"""
    red, green, blue = colors
    return f"\033[38;2;{red};{green};{blue}m{text}"


def get_active_window_name() -> Optional[str]:
    """
    Get the current actibe window name using
    platform specific modules.
    """
    screen = Wnck.Screen.get_default()
    screen.force_update()
    while Gtk.events_pending():
        Gtk.main_iteration()
    active_window = screen.get_active_window()
    if not active_window:
        return None
    process_id = active_window.get_pid()
    read_filename = f"/proc/{process_id}/cmdline"
    with open(read_filename, "r") as file_reader:
        data = file_reader.read()
    return data

def create_notification(title, message, timeout=10):
    notification.notify(title=title, message=message, timeout=timeout)


class Stats(object):
    def get_all_time_stats(self, content) -> Dict[str, str]:
        alltime = {}
        for date in content:
            for application in content[date]:
                if application not in alltime:
                    alltime[application] = 0
                alltime[application] += content[date][application]
        return alltime

    def show_usage_stats(self, content_, date=None, screen_time=None) -> None:
        date = date or datetime.date.today().strftime("%d-%m-%y")
        content = (
            self.get_all_time_stats(content_)
            if date == "all" or date == "alltime"
            else content_.get(date)
        )
        create_time_string = (
            lambda hours, minutes, seconds: f"{hours}:{minutes}:{f'0{seconds}' if seconds < 10 else seconds}"
        )

        if not content:
            print(f"No activity during {date}")
            return None

        print(create_time_string(*self.convert_seconds_to_min(screen_time)))
        table = prettytable.PrettyTable()
        table.field_names = ["Application", "Time Used"]
        for application in content:
            hours, minutes, seconds = __class__.convert_seconds_to_min(
                content.get(application)
            )
            time_string = create_time_string(hours, minutes, seconds)
            table.add_row([application, time_string])
        print(table)

    @staticmethod
    def convert_seconds_to_min(seconds: int) -> Tuple[int, int, int]:
        seconds = seconds % (2 * 3600)
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        return hour, minutes, seconds


class TimeTracker(object):
    total_app_usage: Dict[str, int] = {}
    counter = 0
    date = datetime.date.today().strftime("%d-%m-%y")
    filename = os.path.join(os.path.expanduser("~"), ".time-tracker")

    def __init__(self):
        create_progress_file = not os.path.isfile(self.filename)
        if create_progress_file:
            with open(self.filename, "w") as progress_file_writer:
                progress_file_writer.write("")
        self.total_app_usage = self.read_file_content()

    def get_total_screen_time(self):
        screen_time = 0
        for application in self.total_app_usage[self.date]:
            screen_time += self.total_app_usage[self.date].get(application)
        return screen_time

    def start(self, show_stats):
        '"""Start the time tracker"""'

        APPLICATION_TIME_LIMIT = 7200
        SCREENTIME_LIMIT = 21600

        create_notification("Time Tracker", "Time tracke has started")
        if not self.total_app_usage.get(self.date):
            self.total_app_usage[self.date] = {}
        self.counter = self.get_total_screen_time()
        while True:
            if self.counter > SCREENTIME_LIMIT:
                create_notification(
                    "Titr",
                    f"You have been staring at the screen for almost {int(SCREENTIME_LIMIT / 60 / 60)} hours",
                )
                SCREENTIME_LIMIT += 2
            if show_stats:
                Stats().show_usage_stats(self.total_app_usage, screen_time=self.counter)
            application = get_active_window_name()
            if not application:
                time.sleep(1)
                continue
            application = os.path.basename(application.split(" ")[0])
            if application not in self.total_app_usage[self.date]:
                self.total_app_usage[self.date][application] = 0
            self.total_app_usage[self.date][application] += 1

            if self.total_app_usage[self.date][application] > APPLICATION_TIME_LIMIT:
                name = application[:-1] if application[-1] == "\x00" else application
                time_ = int(APPLICATION_TIME_LIMIT / 60 / 60)
                create_notification(
                    "Titr",
                    f"You have been using {name} for more than {time_} hours today",
                )
                APPLICATION_TIME_LIMIT += 2

            if self.counter % 5 == 0:
                self.log(self.total_app_usage)
            time.sleep(1)
            os.system("clear")
            self.counter += 1

    def log(self, content) -> None:
        with open(self.filename, "w") as file_writer:
            file_writer.write(json.dumps(content))

    def read_file_content(self) -> str:
        with open(self.filename, "r") as file_reader:
            try:
                return json.loads(file_reader.read())
            except Exception as exception:
                self.log({})
                return {}


def argument_parser(arguments: List[str]) -> Tuple[str, Dict[str, str]]:
    command, parameters = None, {}
    for index, element in enumerate(arguments):
        if index == 0:
            command = element
            continue
        is_valid_parameter = element.startswith("--")
        if not is_valid_parameter:
            print(__colored(f"Invalid parameter {element}", RGB_RED))
        slices = element.split("=")
        key, value = slices[0][2:], "=".join(slices[1:])
        parameters.setdefault(key, value)
    return command, parameters


def perform_command(command: str, parameters: Dict[str, str]) -> None:
    tracker = TimeTracker()
    if not command:
        tracker.start(True)
        return None

    if command == "stats":
        date = parameters.get("date")
        stats = Stats()
        stats.show_usage_stats(
            tracker.read_file_content(),
            date=date,
            screen_time=tracker.get_total_screen_time(),
        )
    elif command == "clear":
        tracker.times_used = {}
        tracker.log({})
    elif command == "save":
        filename = input("filename: ")
        with open(filename, "w") as writer:
            writer.write(json.dumps(tracker.times_used))


def main():
    arguments = sys.argv[1:]
    command, params = argument_parser(arguments)
    perform_command(command, params)