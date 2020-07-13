#!/usr/bin/python3
import json
import time
from timer import App, Log, Task
from collections import defaultdict

def duration(seconds):
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    if not hours:
        return f"{minutes:02}:{seconds:02}"
    days, hours = divmod(hours, 24)
    if not days:
        return f"{hours:02}:{minutes:02}:{seconds:02}"
    else:
        return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"

storage = [Log(*val) for val in json.load(open(App.log_filename))]
tasks = [Task(*val) for val in json.load(open(App.task_filename))]

stats = defaultdict(list)
for log in storage:
    stats[log.task].append(log)

for task_id, logs in stats.items():
    print(tasks[task_id])
    prev_day = None
    for log in logs:
        start = time.localtime(log.start)
        if prev_day != start.tm_yday:
            print("\t", time.strftime("%Y-%m-%d", start))
        prev_day = start.tm_yday
        print("\t\t", time.strftime("%H:%M", start), "+", duration(log.end - log.start), log.description)
