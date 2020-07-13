#!/usr/bin/python3
import time
import json
import os.path
from PIL import Image, ImageDraw, ImageFilter
from pystray import Icon, Menu, MenuItem
from collections import namedtuple

def pass_func():
    pass

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

Task = namedtuple("Task", "name project issue_id", defaults=[None, None])
Log = namedtuple("Log", "task start end description", defaults=[None, None])

class App:
    dirname = os.path.expanduser("~/.config/timer")
    log_filename = f"{dirname}/log.json"
    task_filename = f"{dirname}/task.json"
    
    ## Presentation ##
    
    def create_menu(self):
        if self.started:
            title = MenuItem("Zastavit", self.stop, default=True)
        else:
            title = MenuItem(f"Začít {self.task.name}", lambda: self.start(self.task), default=True)
        tasks = [MenuItem(task.name, pass_func) for task in self.recent_tasks()]
        recent = MenuItem("Nedávné...", Menu(*tasks))
        new = MenuItem("Začít úkol...", pass_func)
        return [title, Menu.SEPARATOR, recent, Menu.SEPARATOR, new]
    
    def __init__(self):
        self.icon = Icon("timer", create_image(), title="3:26", menu=Menu(self.create_menu))
        self.task = Task("default task")
        self.started = None
        self.tasks = self.load_tasks()
    
    def run(self):
        self.icon.run()

    ## State ##
    
    def start(self, task):
        self.task = task
        self.started = time.time()
        self.icon.icon = create_image(True)
    
    def stop(self):
        log = Log(self.task, self.started, time.time())
        self.append_log(log)
        self.started = None
        self.icon.icon = create_image(False)
    
    ## Repository ##
    
    def load_tasks(self):
        os.makedirs(self.dirname, exist_ok=True)
        try:
            return [Task(*values) for values in json.load(open(self.task_filename))]
        except (IOError, ValueError):
            return list()
    
    def append_log(self, log):
        task_id = self.task_id(log.task)
        try:
            storage = json.load(open(self.log_filename))
        except (IOError, ValueError):
            storage = list()
        storage.append(log._replace(task=task_id))
        with open(self.log_filename, "w+") as f:
            json.dump(storage, fp=f, indent=2)
    
    def task_id(self, task):
        if task not in self.tasks:
            self.tasks.append(task)
            with open(self.task_filename, "w+") as f:
                json.dump(self.tasks, fp=f, indent=2)
        return self.tasks.index(task)
    
    def recent_tasks(self):
        return self.tasks

if __name__ == "__main__":
    App().run()
