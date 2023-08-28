import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException


HELP = 'Usage:\npython tpaths_cleanse.py --dbpath="<database path>"\n'

def cleanse(conn: sqlite3.Connection):
  """Unlabels token paths which refer to unlabelled paths."""
  
  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  try:
    # get all token paths missing labelling in paths
    c.execute("SELECT * FROM (SELECT * FROM token_paths WHERE names_func IS NOT NULL) LEFT JOIN paths ON path_id = id WHERE to_name IS NULL")
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  # get all labelled negative function-token paths
  tpaths = c.fetchall()
  path_id = 0
  token_literal = ""
  count = 0
  for tpath in tpaths:
    path_id = tpath[0]
    token_literal = tpath[3]
    
    try:
      c.execute("UPDATE token_paths SET names_func = NULL WHERE path_id = ? AND token_literal = ?", (path_id, token_literal))
    # 'no such table: token_paths'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()
    
    count += 1
    print(f"{count}. {path_id} {token_literal}")

  print(f"Unlabelled {count} token paths missing path labelling")
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
  cleanse(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
