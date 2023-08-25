import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException
from tokens.lexer import Lexer
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer, tokenize

HELP = 'Usage:\npython tpaths_add_missing_pos.py --dbpath="<database path>"\n'

def add_missing_positives(conn: sqlite3.Connection):
  """Adds missing token paths from `paths` positives to `token_paths_positive` to be labelled and merged into `token_paths`."""

  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  # Create function-token xrefs table
  c.execute('''CREATE TABLE IF NOT EXISTS token_paths_positive (
              path_id INTEGER NOT NULL,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              token_literal TEXT NOT NULL,
              names_func INTEGER)''')
  
  # get path positives missing token paths
  try:
    c.execute('''SELECT * FROM (SELECT * FROM paths WHERE to_name = 1) LEFT JOIN token_paths ON id = path_id WHERE token_literal IS NULL''')
    missing_pos = c.fetchall()
  except:
    raise DbException("Missing `paths` table")
  
  # get unlabelled paths of a function positive
  count = 0
  for path in missing_pos:
    path_id = path[0]
    func_addr = path[1]
    string_addr = path[2]
    lexer = Lexer("")
    parser = PreParser([])
    tokenizer = Tokenizer([])

    c.execute("SELECT literal FROM strings WHERE address = ?", (string_addr,))
    string_literal = c.fetchone()
    # line vars - skip bad path data
    if string_literal is None:
      print(f"Referenced string at {hex(string_addr)} doesn't exist in the database (likely a duplicate)")
      continue

    tokens = tokenize(string_literal[0], lexer, parser, tokenizer)
  
    for token in tokens:
      try:
        c.execute("INSERT INTO token_paths_positive (path_id,func_addr,string_addr,token_literal) VALUES (?,?,?,?)", (path_id, func_addr, string_addr, token.token))
        count += 1
      # 'no such table: token_paths'
      except sqlite3.OperationalError as ex:
        print(ex)
        sys.exit()
      print(f"{count}.\t{path_id}\t{token.token}")

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
  add_missing_positives(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
