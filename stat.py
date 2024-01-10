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


def main(start=0, project=None):
    total = 0
    for task, end in db(Log).group_by('task', end='max(end)'):
        logs = db(Log).read(task_eq=task, end_ge=start)
        if not logs:
            continue
        if project and task.project != project:
            continue
        task_total = sum(log.end - log.start for log in logs)
        print(task, pretty_duration(task_total))
        group_by_day = listdict((pretty_day(log.start), log) for log in logs)
        for day, day_logs in group_by_day.items():
            print("\t", day, pretty_duration(sum(log.end - log.start for log in day_logs)))
            for log in day_logs:
                print("\t\t", pretty_minute(log.start), "+", pretty_duration(log.end - log.start), log.description)
        total += task_total
    print("Total time shown:", pretty_duration(total))


if __name__ == "__main__":
    from sys import argv
    if len(argv) == 1:
        main()
    elif argv[1] == "-h" or argv[1] == "--help":
        print("USAGE: stat.py [period [project]]")
        print("  period may be: 'day', 'week', 'month', 'year' or a starting date like '2018-01-01'")
    else:
        day = 24*3600
        period = {"day": day, "week": 7*day, "month": 31*day, "year": 366*day}.get(argv[1])
        if period is None:
            start = time.mktime(time.strptime(argv[1], "%Y-%m-%d"))
        else:
            start = time.time() - period
        project = argv[2] if len(argv) > 2 else None
        main(start, project)
