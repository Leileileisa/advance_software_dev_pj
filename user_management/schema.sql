DROP TABLE IF EXISTS user;

CREATE TABLE user (
  id INTEGER PRIMARY KEY ,
  password TEXT NOT NULL check(length(password)<10)
);