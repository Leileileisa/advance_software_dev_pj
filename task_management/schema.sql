DROP TABLE IF EXISTS task;

CREATE TABLE task (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user TEXT UNIQUE NOT NULL ,
  department TEXT NOT NULL ,
  task_unfinished INTEGER DEFAULT 1
);