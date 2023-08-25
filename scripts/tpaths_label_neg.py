import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException


HELP = 'Usage:\npython tpaths_label_neg.py --dbpath="<database path>"\n'

def label_negative(conn: sqlite3.Connection):
  """Adds missing labels of negative token paths (based on `paths` labels)."""
  
  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  try:
    # get all negative token paths missing labelling in token paths
    c.execute("SELECT * FROM (SELECT * FROM paths WHERE to_name = 0) JOIN token_paths ON id = path_id WHERE token_literal IS NOT NULL AND names_func IS NULL")
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  # get all labelled negative function-token paths
  path_negs = c.fetchall()
  path_id = 0
  token_literal = ""
  count = 0
  for path in path_negs:
    count += 1
    path_id = path[0]
    token_literal = path[12]
    print(f"{count}.\t{path_id}\t{token_literal}")
    
    try:
      c.execute("UPDATE token_paths SET names_func = 0 WHERE path_id = ? AND token_literal = ?", (path_id, token_literal))
    # 'no such table: token_paths'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

  print(f"Labelled {count} missing negative token paths")
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
  label_negative(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
