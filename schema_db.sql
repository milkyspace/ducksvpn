CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE payments (id INTEGER PRIMARY KEY AUTOINCREMENT, tgid INTEGER UNIQUE ON CONFLICT IGNORE, bill_id TEXT, amount INTEGER, time_to_add BIGINT, mesid TEXT);
CREATE TABLE userss (id INTEGER PRIMARY KEY AUTOINCREMENT, tgid INTEGER UNIQUE ON CONFLICT IGNORE, subscription TEXT DEFAULT none, banned BOOLEAN DEFAULT (false), notion_oneday BOOLEAN DEFAULT (false), username STRING DEFAULT none, fullname STRING DEFAULT none, wg_key TEXT, trial_continue integer, referrer_id INTEGER DEFAULT none);

CREATE TABLE IF NOT EXISTS payments (
  id int NOT NULL PRIMARY KEY,
  tgid varchar(50),
  bill_id text,
  amount int,
  time_to_add bigint,
  mesid text
);
CREATE TABLE IF NOT EXISTS userss (
  id int NOT NULL PRIMARY KEY,
  tgid varchar(50),
  subscription text,
  banned BOOL NOT NULL DEFAULT FALSE,
  username varchar(50),
  fullname varchar(50),
  trial_continue BOOL NOT NULL DEFAULT FALSE,
  referrer_id int
);