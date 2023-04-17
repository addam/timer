from collections import defaultdict, namedtuple
import csv
from functools import cache
import operator
import os


def is_dataclass(tp):
  return hasattr(tp, "__annotations__")


class Svorm:
  def __init__(self, dirname):
    os.makedirs(dirname, exist_ok=True)
    self.dirname = dirname

  def field_constructors(self, cls):
    return [(name, self(tp).read_one if is_dataclass(tp) else tp) for name, tp in cls.__annotations__.items()]

  @cache
  def __call__(self, cls):
    filename = f"{self.dirname}/{cls.__name__.lower()}.csv"
    return Table(cls, filename, self)

  def delete(self, delete_items, cascade=[]):
    """Safely delete several items from arbitrary tables, with cascading."""
    resolved_ids = defaultdict(set)
    cascade_tables = [self(tp) for tp in cascade]
    while delete_items:
      item = delete_items.pop()
      for table in cascade_tables:
        delete_items.extend(table.read(any=item))
      tp = type(item)
      resolved_ids[tp].add(self(tp).get_id(item))
    print("will delete", resolved_ids)
    for tp, ids in resolved_ids.items():
      table = self(tp)
      table._delete_ids(ids)
      for tp2, missing_ids in resolved_ids.items():
        for name in table.fields_of_type(tp2):
          table._shift_ids(name, missing_ids)


def refreshing(source):
  def call(self, *args, **kwargs):
    if hasattr(self, "last_refreshed"):
      tm = os.path.getmtime(self.filename)
      if tm > self.last_refreshed:
        self.last_refreshed = tm
        self._refresh()
    return source(self, *args, **kwargs)
  return call


class VirtualTable:
  def __init__(self, cls, rows):
    self.cls, self.rows = cls, rows

  @refreshing
  def get_id(self, item):
    return self.rows.index(item)

  @refreshing
  def read_one(self, id):
    return self.rows[int(id)]

  @refreshing
  def read(self, **kwargs):
    result = list(self.rows)
    for key, value in kwargs.items():
      match key.rsplit("_", 1):
        case ["limit"]:
          result = result[:value]
        case ["order"]:
          name = value[0]
          reverse = len(value) > 1 and value[1] == "desc"
          result = sorted(result, key=lambda x: getattr(x, name), reverse=reverse)
        case ["any"]:
          fields = self.fields_of_type(type(value))
          result = [x for x in result if any(getattr(x, name) == value for name in fields)]
        case [name, ("eq" | "lt" | "gt" | "le" | "ge" | "ne") as op]:
          func = getattr(operator, op)
          result = [x for x in result if func(getattr(x, name), value)]
    return result


class Table(VirtualTable):
  def __init__(self, cls, filename, db):
    self.cls, self.filename, self.db = cls, filename, db
    self.rows = None
    self.last_refreshed = 0

  def raw_reader(self):
    reader = csv.reader(open(self.filename))
    return filter(None, reader)

  def _refresh(self):
    fields = self.db.field_constructors(self.cls)
    self.rows = [self.cls(*[tp(value) for value, (name, tp) in zip(line, fields)]) for line in self.raw_reader()]

  def fields_of_type(self, item_cls):
    return [name for name, tp in self.cls.__annotations__.items() if tp == item_cls]

  def create(self, item):
    typed_values = [(tp, getattr(item, name)) for name, tp in self.cls.__annotations__.items()]
    data = [self.db(tp).get_id(value) if is_dataclass(tp) else value for tp, value in typed_values]
    with open(self.filename, "a+") as f:
      csv.writer(f).writerow(data)
    return item

  def _delete_ids(self, ids):
    """Deletes some items by their row ids, without cascading. Will break all linked foreign keys."""
    reader = self.raw_reader()
    data = [line for i, line in enumerate(reader) if i not in ids]
    with open(self.filename, "w+") as f:
      csv.writer(f).writerows(data)

  def _shift_ids(self, name, ids):
    """Update a foreign key after some foreign ids have been deleted"""
    def shift(value):
      i = int(value)
      return i - sum(j < i for j in ids)

    # trying to keep `names` in sync with other parts of code where __annotations__ are used
    names = [n for n, _ in self.cls.__annotations__.items()]
    reader = self.raw_reader()
    data = [[shift(v) if n == name else v for n, v in zip(names, line)] for line in reader]
    with open(self.filename, "w+") as f:
      csv.writer(f).writerows(data)

  def group_by(self, name, **kwargs):
    aggregators = {fn.__name__: fn for fn in [min, max, sum]}
    fields = (name, *kwargs)
    cls = namedtuple(f"{self.cls.__name__}Group", fields)
    expressions = [expr.split("(", 1) for expr in kwargs.values()]
    field_constructors = [(aggregators[fn], col.rstrip(")")) for fn, col in expressions]
    groups = defaultdict(list)
    for item in self.read():
      groups[getattr(item, name)].append(item)
    data = list()
    for key, items in groups.items():
      values = [fn(getattr(x, col) for x in items) for fn, col in field_constructors]
      data.append(cls(key, *values))
    return VirtualTable(cls, data)


def test():
  from dataclasses import dataclass

  @dataclass
  class Parent:
    name: str
    weight: float

  @dataclass
  class Child:
    parent: Parent
    age: int

  db = Svorm("./test")
  children = db(Child)
  joe = db(Parent).create(Parent("Joe", 57.4))
  children.create(Child(joe, 7))
  children.create(Child(joe, 12))
  print(children.read(parent_eq=joe, order=('age', 'desc'), limit=3))
  db.delete([joe], [Parent, Child])


if __name__ == "__main__":
  test()  
