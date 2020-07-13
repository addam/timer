#!/usr/bin/python3
import time
import json
import os.path
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem
from collections import namedtuple

def pass_func():
    pass

def create_image(is_running=False):
    size = 16
    fg = "#dfdbd2ff"
    red = "#f00"
    image = Image.new('RGBA', (size, size), "#0000")
    dc = ImageDraw.Draw(image)
    if is_running:
        bbox = [(0, 0), (size, size)]
        dc.ellipse(bbox, fill=red)
    else:
        triangle = [(size // 4, 0), (size // 4, size), (3 * size // 4, size // 2)]
        dc.polygon(triangle, fill=fg)
    return image

Task = namedtuple("Task", "name project issue_id", defaults=[None, None])
Log = namedtuple("Log", "task start end description", defaults=[None, None])

class Controller:
    def create_menu(self):
        if self.state.started:
            title = MenuItem("Zastavit", self.state.stop, default=True)
        else:
            title = MenuItem(f"Začít {self.state.task.name}", lambda: self.state.start(self.state.task), default=True)
        tasks = [MenuItem(task.name, pass_func) for task in self.repo.recent_tasks()]
        new = MenuItem("Začít úkol...", pass_func)
        return [title, Menu.SEPARATOR, *tasks, Menu.SEPARATOR, new]
    
    def __init__(self):
        self.repo = Repository()
        self.state = State(self.repo)
        self.icon = Icon("timer", create_image(), title="3:26", menu=Menu(self.create_menu))
    
    def run(self):
        self.icon.run()

class State:
    def __init__(self, repo):
        self.repo = repo
        self.task = Task("default task")
        self.started = None
    
    def start(self, task):
        self.task = task
        self.started = time.time()
    
    def stop(self):
        self.log = Log(self.task, self.started, time.time())
        self.repo.append(self.log)
        self.started = None
    
class Repository:
    dirname = os.path.expanduser("~/.config/timer")
    log_filename = f"{dirname}/log.json"
    task_filename = f"{dirname}/task.json"
    
    def __init__(self):
        os.makedirs(self.dirname, exist_ok=True)
        try:
            self.tasks = [Task(*values) for values in json.load(open(self.task_filename))]
        except (IOError, ValueError):
            self.tasks = list()
    
    def append(self, log):
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
    Controller().run()
