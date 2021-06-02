#!/usr/bin/python3
import csv
import time
from timer import App, Log, Task, duration
from collections import defaultdict

def listdict(seq):
    result = defaultdict(list)
    for key, value in seq:
        result[key].append(value)
    return result

def read_csv(file, fields):
    typedict = {"s": str, "i": int, "f": float}
    types = [typedict[tp] for tp in fields]
    for line in csv.reader(file):
        yield [tp(val) if val else None for tp, val in zip(types, line)]

def format_day(timestamp):
    return time.strftime("%Y-%m-%d", time.localtime(timestamp))

storage = [Log(*val) for val in read_csv(open(App.log_filename), "iffs")]
tasks = [Task(*val) for val in read_csv(open(App.task_filename), "ssi")]

stats = defaultdict(list)
for log in storage:
    stats[log.task].append(log)

def thread_latest(logs):
    return max(log.end for log in logs)

for task_id, logs in sorted(stats.items(), key=lambda pair: thread_latest(pair[1])):
    try:
        print(tasks[task_id], duration(sum(log.end - log.start for log in logs)))
    except IndexError:
        print(f"task {task_id} not in list")
    group_by_day = listdict((format_day(log.start), log) for log in logs)
    for day, day_logs in group_by_day.items():
        print("\t", day, duration(sum(log.end - log.start for log in day_logs)))
        for log in day_logs:
            start = time.localtime(log.start)
            print("\t\t", time.strftime("%H:%M", start), "+", duration(log.end - log.start), log.description)
    
