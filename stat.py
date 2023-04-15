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


def thread_latest(logs):
    return max(log.end for log in logs)

def main(start=0):
    storage = [Log(*val) for val in read_csv(open(App.log_filename), "iffs")]
    tasks = [Task(*val) for val in read_csv(open(App.task_filename), "sss")]

    stats = defaultdict(list)
    for log in storage:
        if log.end >= start:
            stats[log.task].append(log)

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

if __name__ == "__main__":
    from sys import argv
    if len(argv) == 1:
        main()
    elif argv[1] == "-h":
        print("USAGE: stat.py [period]")
        print("  period may be: 'day', 'week', 'month', 'year'")
    else:
        day = 24*3600
        period = {"day": day, "week": 7*day, "month": 31*day, "year": 366*day}[argv[1]]
        main(time.time() - period)
