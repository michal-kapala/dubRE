import os, sys, getopt
import sqlite3
import datetime
from tokens.lexer import Lexer
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer, tokenize
from utils.db import DbException


HELP = 'Usage:\npython tokenize_one.py --dbpath="<database path>" --offset=<string offset>'

def check_columns(c: sqlite3.Cursor):
  """Validates column integrity of `strings`table."""
  try:
    c.execute("SELECT * FROM pragma_table_info('strings') WHERE name='address' OR name='literal'")
  except Exception as ex:
    print(ex)
    sys.exit()

  columns = c.fetchall()

  if len(columns) == 0:
    raise DbException("Missing columns: address, literal")
  
  if len(columns) == 1:
    if columns[0][1] == "address":
      raise DbException("Missing column: literal")
    else:
      raise DbException("Missing column: address")
    
  if columns[0][1] == "address" and columns[0][2] != "INTEGER":
    raise DbException("Invalid 'address' column type, required: INTEGER")
  if columns[0][1] == "literal" and columns[0][2] != "TEXT":
    raise DbException("Invalid 'literal' column type, required: TEXT")

def make_tokens(conn: sqlite3.Connection, offset: int):
  """Creates `tokens` from a single string."""
  c = conn.cursor()
  try:
    c.execute("SELECT * FROM strings WHERE address = ?", (offset,))
  # 'no such table: strings'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  string = c.fetchone()

  # table integrity check
  check_columns(c)

  # create 'tokens' table
  # duplicates are okay since if a token is a function name can depend on its context
  # UNIQUE constraint is used to shrink the token dataset significantly (>50% for large binaries)
  # and remove mostly useless information (discriminates short function names like read, puts, exit etc.)
  c.execute('''CREATE TABLE IF NOT EXISTS tokens
              (string_addr integer NOT NULL, literal text UNIQUE, is_name integer)''')

  print(f"start:\t{datetime.datetime.now()}")
  # produce tokens
  address = string[0]
  literal = string[1]
  tokens = tokenize(literal, Lexer(""), PreParser([]), Tokenizer([]))

  # add token records
  for t in tokens:
    try:
      c.execute("INSERT INTO tokens (string_addr, literal) VALUES (?,?)", (address, t.token))
    # Skip duplicate errors on UNIQUE db constraint ('UNIQUE constraint failed: tokens.literal')
    except sqlite3.IntegrityError:
      pass
    except Exception as ex:
      print(ex)
      break
  
  conn.commit()
  conn.close()

  print(f"end:\t{datetime.datetime.now()}")

def main(argv):
  db_path = ""
  offset = None
  opts, args = getopt.getopt(argv,"hdo:",["dbpath=", "offset="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-o", "--offset"):
      offset = int(arg)

  if db_path == "":
    raise DbException(f"SQLite database path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise DbException(f"Database not found at {db_path}")
  if offset is None or offset == 0:
    raise Exception(f"Invalid string offset: {offset}")

  conn = sqlite3.connect(db_path)
  make_tokens(conn, offset)

if __name__ == "__main__":
   main(sys.argv[1:])
