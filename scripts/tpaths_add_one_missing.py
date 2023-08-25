import os, sys, getopt
import sqlite3
from datetime import datetime
from utils.db import DbException
from tokens.lexer import Lexer
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer, tokenize


HELP = 'Usage:\npython tpaths_add_one_missing.py --dbpath="<database path>" --pathid=<path id>\n'

def add_one_missing(conn: sqlite3.Connection, id: int):
  """Adds missing `tokens` and `token_paths` of a single unlabelled string referenced by a path."""
  
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
    c.execute("SELECT * FROM paths WHERE id = ?", (id,))
    path = c.fetchone()
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  if path is None:
    print("Invalid path id")
    sys.exit()

  func_addr = path[1]
  string_addr = path[2]

  try:
    c.execute("SELECT literal FROM strings WHERE address = ?", (string_addr,))
    string_literal = c.fetchone()
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  if string_literal is None:
    print("Referenced string doesn't exist in the database")
    sys.exit()

  string_literal = string_literal[0]

  lexer = Lexer("")
  parser = PreParser([])
  tokenizer = Tokenizer([])

  tokens = tokenize(string_literal, lexer, parser, tokenizer)

  for token in tokens:
    try:
      try:
        c.execute("INSERT INTO tokens (string_addr,literal) VALUES (?,?)", (string_addr, token.token))
      # UNIQUE contraint failed: tokens.literal - skip duplicates
      except sqlite3.IntegrityError:
        print(f"Duplicate token: {token.token}")

      c.execute("INSERT INTO token_paths (path_id,func_addr,string_addr,token_literal) VALUES (?,?,?,?)", (id, func_addr, string_addr, token.token))
    # 'no such table: token_paths'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

  print(f"end:\t{datetime.now()}")

  conn.commit()

def main(argv):
  db_path = ""
  id = ""
  opts, args = getopt.getopt(argv,"hdp:",["dbpath=", "pathid="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-p", "--pathid"):
      id = arg

  if db_path == "":
    raise DbException(f"SQLite database path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise DbException(f"Database not found at {db_path}")
  
  conn = sqlite3.connect(db_path)
  add_one_missing(conn, int(id))
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])
