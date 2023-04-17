import os
from dataclasses import dataclass
from svorm import Svorm
import time

dirname = os.path.expanduser("~/.config/timer")
db = Svorm(dirname)


@dataclass(unsafe_hash=True)
class Task:
  name: str
  project: str = ""
  issue_id: str = ""


@dataclass
class Log:
  task: Task
  start: float
  end: float
  description: str = ""


def test():
  logs = db(Log)
  print(logs.group_by('task', end='max(end)').read(limit=20, order=('end', 'desc')))
  start = time.time() - 24 * 3600
  print(logs.read(end_gt=time.time() - start))


if __name__ == "__main__":
  test()
