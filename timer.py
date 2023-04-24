#!/usr/bin/python3
from collections import namedtuple
import csv
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib
import os.path
from PIL import Image, ImageDraw, ImageFilter
from pystray import Icon, Menu, MenuItem
from repo import db, Log, Task
import time


def create_image(is_running=False):
    size = 16
    fg = "#dfdbd2ff"
    red = "#f00"
    image = Image.new('RGBA', (2*size, 2*size), "#0000")
    dc = ImageDraw.Draw(image)
    if is_running:
        bbox = [(2, 2), (2*size-4, 2*size-4)]
        dc.ellipse(bbox, fill=red)
    else:
        triangle = [(size // 2, 0), (size // 2, 2*size), (3 * size // 2, size)]
        dc.polygon(triangle, fill=fg)
    image = image.resize((size, size))
    return image

def pretty_duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    if not days:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"


class App:
    def __init__(self):
        # State
        self.started = None
        self.task = next(iter(self.recent_tasks()), Task("default task"))
        # Presentation
        self.icon = Icon("timer", create_image(), title="dummy title", menu=Menu(self.create_menu))
        orig_fn = self.icon._create_menu
        def impostor(*args, **kwargs):
            result = orig_fn(*args, **kwargs)
            self.set_click_callback()
            return result
        self.icon._create_menu = impostor

    ## State

    def start(self, task):
        self.task = task
        self.started = time.time()
        self.icon.icon = create_image(True)
        self.set_click_callback()

    def stop(self):
        log = Log(self.task, self.started, time.time())
        log = db.create(log)
        self.started = None
        self.icon.icon = create_image(False)

    def recent_tasks(self):
        tasks = db(Log).group_by('task', end='max(end)').read(order=('end', 'desc'), limit=20)
        return [x.task for x in tasks]

    def elapsed(self):
        return time.time() - self.started

    ## Presentation

    def create_menu(self):
        def starter(task):
            def func(icon):
                self.start(task)
            return func

        if self.started:
            title = MenuItem(f"Zastavit {self.task.name}", self.stop, default=True)
        else:
            title = MenuItem(f"Začít {self.task.name}", starter(self.task), default=True)
        tasks = [MenuItem(task.name, starter(task)) for task in self.recent_tasks()]
        recent = MenuItem("Nedávné...", Menu(*tasks))
        new = MenuItem("Začít úkol...", self.run_new_task_dialog)
        return [title, Menu.SEPARATOR, recent, Menu.SEPARATOR, new]

    def set_click_callback(self):
        def update_label(menu):
            if not self.started:
                return
            label = f"Zastavit {self.task.name} ({pretty_duration(self.elapsed())})"
            # get the first menu item
            item = next(iter(menu))
            GLib.idle_add(item.set_label, label)

        def postponed():
            self.icon._menu_handle.connect('show', update_label)

        GLib.idle_add(postponed)

    def run_new_task_dialog(self, icon):
        dialog = Gtk.Dialog(parent=None, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_title("Začít úkol...")
        box = dialog.get_content_area()
        name_entry, project_entry, issue_id_entry = entries = [Gtk.Entry() for i in range(3)]
        for entry, title in zip(entries, ["Úkol", "Projekt", "Issue ID"]):
            box.add(Gtk.Label(label=title))
            box.add(entry)
        dialog.show_all()
        response = dialog.run()
        task = Task(name_entry.get_text(), project_entry.get_text(), issue_id_entry.get_text())
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            self.start(task)

    def run(self):
        self.icon.run()


if __name__ == "__main__":
    from sys import argv
    match argv[1:]:
        case ["--task", name]:
            for task in db(Task).read(name_eq=name):
                print(task)
                for log in db(Log).read(task_eq=task):
                    print(" ", log)
        case ["--project"]:
            for row in db(Task).group_by('project'):
                print(row.project)
        case ["--project", name]:
            for task in db(Task).read(project_eq=name):
                print(task)
                for log in db(Log).read(task_eq=task):
                    print(" ", log)
        case ["--delete-task", name]:
            victims = db(Task).read(name_eq=name)
            db.delete(victims, [Log])
            print("deleted", victims)
        case ["--delete-project", name]:
            victims = db(Task).read(project_eq=name)
            db.delete(victims, [Log])
            print("deleted", victims)
        case ["--last"]:
            victims = db(Log).read(order=('end', 'desc'), limit=1)
            print(*victims)
        case ["--delete-last"]:
            victims = db(Log).read(order=('end', 'desc'), limit=1)
            db.delete(victims, [Log])
            print("deleted", victims)
        case []:
            print("run", argv)
            App().run()
        case _:
            print("usage: ./timer.py --task <name> | --project <name> | --delete-task <name> | --delete-project <name> | -h")
        
