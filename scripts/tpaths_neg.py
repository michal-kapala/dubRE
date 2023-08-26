import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException
from tokens.lexer import Lexer
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer, tokenize


HELP = 'Usage:\npython tpaths_neg.py --dbpath="<database path>"\n'

def make_token_paths_negative(conn: sqlite3.Connection):
  """Adds and autolabels negative `token_paths` (based on `paths` labels)."""
  
  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  # Create function-token xrefs table
  c.execute('''CREATE TABLE IF NOT EXISTS token_paths (
              path_id INTEGER NOT NULL,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              token_literal TEXT NOT NULL,
              names_func INTEGER)''')

  try:
    # get all negative paths missing token paths
    c.execute("SELECT * FROM (SELECT * FROM paths WHERE to_name = 0) LEFT JOIN token_paths ON id = path_id WHERE token_literal IS NULL")
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  # get all labelled negative function-string paths
  path_negs = c.fetchall()
  lexer = Lexer("")
  parser = PreParser([])
  tokenizer = Tokenizer([])
  count = 0

  for path in path_negs:
    path_id = path[0]
    func_addr = path[1]
    string_addr = path[2]

    c.execute("SELECT literal FROM strings WHERE address = ?", (string_addr,))
    string_literal = c.fetchone()
    # line vars - skip bad path data
    if string_literal is None:
      print(f"Referenced string at {hex(string_addr)} doesn't exist in the database (likely a duplicate)")
      continue

    tokens = tokenize(string_literal[0], lexer, parser, tokenizer)
    
    for token in tokens:
      try:
        c.execute("INSERT INTO token_paths VALUES (?,?,?,?,?)", (path_id, func_addr, string_addr, token.token, 0))
        count += 1
      # 'no such table: token_paths'
      except sqlite3.OperationalError as ex:
        print(ex)
        sys.exit()
      print(f"{count}.\t{path_id}\t{token.token}")

  print(f"Added and labelled {count} missing negative token paths")
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
  make_token_paths_negative(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
