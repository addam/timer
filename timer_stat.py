#!/usr/bin/python3
import csv
import time
from timer import App, Log, Task, duration
from collections import defaultdict

def read_csv(file, fields):
    typedict = {"s": str, "i": int, "f": float}
    types = [typedict[tp] for tp in fields]
    for line in csv.reader(file):
        yield [tp(val) if val else None for tp, val in zip(types, line)]

storage = [Log(*val) for val in read_csv(open(App.log_filename), "iffs")]
tasks = [Task(*val) for val in read_csv(open(App.task_filename), "ssi")]

stats = defaultdict(list)
for log in storage:
    stats[log.task].append(log)

for task_id, logs in stats.items():
    print(tasks[task_id], duration(sum(log.end - log.start for log in logs)))
    prev_day = None
    for log in logs:
        start = time.localtime(log.start)
        if prev_day != start.tm_yday:
            print("\t", time.strftime("%Y-%m-%d", start))
        prev_day = start.tm_yday
        print("\t\t", time.strftime("%H:%M", start), "+", duration(log.end - log.start), log.description)
