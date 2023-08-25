import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException


HELP = 'Usage:\npython autolabel_paths.py --dbpath=<database path>\n'

def autolabel(conn: sqlite3.Connection):
  """Searches for positive token literal references and pdb functions including the token. Labels `paths` records SQLite table based on found paths."""
  
  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  try:
    c.execute("SELECT * FROM tokens WHERE is_name = 1")
  # 'no such table: tokens'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  tokens = c.fetchall()
  tkn_cnt = 0

  # for every positive token
  for token in tokens:
    tkn_cnt += 1
    string_addr = token[0]
    token_literal = token[1]
    print(f"{tkn_cnt} - {token_literal}")
    try:
      c.execute(f"SELECT * FROM pdb WHERE literal LIKE '%{token_literal}%'")
    # 'no such table: pdb'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()
    funcs = c.fetchall()
    
    # for every function including the token
    for func in funcs:
      func_addr = func[0]
      try:
        c.execute("SELECT * FROM paths WHERE func_addr = ? AND string_addr = ?", (func_addr, string_addr))
      # 'no such table: paths'
      except sqlite3.OperationalError as ex:
        print(ex)
        sys.exit()
      paths = c.fetchall()

      # label found paths positive
      for path in paths:
        try:
          c.execute("UPDATE paths SET to_name = 1 WHERE id = ?", (path[0],))
        # 'no such table: paths'
        except sqlite3.OperationalError as ex:
          print(ex)
          sys.exit()

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
  autolabel(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
