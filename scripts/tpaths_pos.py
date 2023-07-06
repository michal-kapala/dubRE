import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException
from tokens.lexer import Lexer
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer, tokenize


HELP = 'Usage:\npython tpaths_pos.py --dbpath=<database path>\n'

def make_token_paths_positive(conn: sqlite3.Connection):
  """Populates `token_paths_positive` SQLite helper table (for manual labelling)."""
  
  print(f"start:\t{datetime.now()}")

  c = conn.cursor()

  # Create function-token xrefs table
  c.execute('''CREATE TABLE IF NOT EXISTS token_paths_positive (
              path_id INTEGER NOT NULL,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              token_literal TEXT NOT NULL,
              names_func INTEGER)''')

  try:
    c.execute("SELECT * FROM (SELECT * FROM tokens WHERE is_name = 1) AS tokens LEFT JOIN (SELECT * FROM paths WHERE to_name = 1) AS paths ON tokens.string_addr = paths.string_addr WHERE id IS NOT NULL")
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  # get all positive function-string paths
  tpath_positives = c.fetchall()
  lexer = Lexer("")
  parser = PreParser([])
  tokenizer = Tokenizer([])

  for path in tpath_positives:
    path_id = path[3]
    func_addr = path[4]
    string_addr = path[5]

    c.execute("SELECT literal FROM strings WHERE address = ?", (string_addr,))
    string_literal = c.fetchone()
    # line vars - skip bad path data
    if string_literal is None:
      continue

    tokens = tokenize(string_literal[0], lexer, parser, tokenizer)

    for token in tokens:
      try:
        c.execute("INSERT INTO token_paths_positive (path_id,func_addr,string_addr,token_literal) VALUES (?,?,?,?)", (path_id, func_addr, string_addr, token.token))
      # 'no such table: token_paths_positive'
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
  make_token_paths_positive(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
