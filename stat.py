#!/usr/bin/python3
from collections import defaultdict
import csv
from repo import db, Log, Task
import time
from timer import pretty_duration


def listdict(seq):
    result = defaultdict(list)
    for key, value in seq:
        result[key].append(value)
    return result

def pretty_day(timestamp):
    return time.strftime("%Y-%m-%d", time.localtime(timestamp))

def pretty_minute(timestamp):
    return time.strftime("%H:%M", time.localtime(timestamp))


def main(start=0):
    for task, end in db(Log).group_by('task', end='max(end)'):
        logs = db(Log).read(task_eq=task, end_ge=start)
        if not logs:
            continue
        print(task, pretty_duration(sum(log.end - log.start for log in logs)))
        group_by_day = listdict((pretty_day(log.start), log) for log in logs)
        for day, day_logs in group_by_day.items():
            print("\t", day, pretty_duration(sum(log.end - log.start for log in day_logs)))
            for log in day_logs:
                print("\t\t", pretty_minute(log.start), "+", pretty_duration(log.end - log.start), log.description)


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
