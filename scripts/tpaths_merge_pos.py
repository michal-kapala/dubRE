import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException


HELP = 'Usage:\npython tpaths_merge_pos.py --dbpath=<database path>\n'

def merge_token_paths(conn: sqlite3.Connection):
  """Copies positive labels from `token_paths_positive` SQLite helper table into `token_paths` table and deletes `token_paths_positive`."""
  
  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  try:
    c.execute("SELECT * FROM token_paths_positive")
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  # get all positive function-string paths
  positive_paths = c.fetchall()

  for path in positive_paths:
    path_id = path[0]
    token = path[3]
    label = path[4]

    try:
      c.execute("UPDATE token_paths SET names_func = ? WHERE path_id = ? AND token_literal = ?", (label, path_id, token))
    # 'no such table: token_paths'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

  conn.commit()

  # delete the helper table
  c.execute("DROP TABLE token_paths_positive")
  print(f"end:\t{datetime.now()}")

  conn.commit()

def main(argv):
  db_path = ""
  opts, args = getopt.getopt(argv,"hd:",["dbpath="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg

  if db_path == "":
    raise DbException(f"SQLite database path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise DbException(f"Database not found at {db_path}")
  
  conn = sqlite3.connect(db_path)
  merge_token_paths(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
