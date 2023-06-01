import os, sys, getopt
import sqlite3
from idatokens.lexer import Lexer
from idatokens.preparser import PreParser
from idatokens.tokenizer import Tokenizer
import datetime

HELP = 'Usage:\npython tokenize_idb.py -d <database path>'

class DbException(Exception):
  """SQLite database exception."""
  def __init__(self, message):            
    super().__init__(message)

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

def tokenize(conn: sqlite3.Connection):
  c = conn.cursor()
  try:
    c.execute("SELECT * FROM strings")
  # 'no such table: strings'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  strings = c.fetchall()

  # table integrity check
  check_columns(c)

  # create 'tokens' table
  # duplicates are okay since if a token is a function name can depend on its context
  # UNIQUE constraint is used to shrink the token dataset significantly (>50% for large binaries)
  # and remove mostly useless information (discriminates short function names like read, puts, exit etc.)
  c.execute('''CREATE TABLE IF NOT EXISTS tokens
              (string_addr integer NOT NULL, literal text UNIQUE, is_name integer)''')

  print(f"start:\t{datetime.datetime.now()}")
  # process strings
  lexer = Lexer("")
  preparser = PreParser([])
  tokenizer = Tokenizer([])

  for address, string in strings:
    lexer.reset(string)
    # create metatokens
    metatokens = lexer.metatokens()
    preparser.reset(metatokens)
    # join operator metatokens into operator identifiers
    metatokens = preparser.make_operator_ids()
    preparser.reset(metatokens)
    # create template-like tokens
    metatokens = preparser.make_templates()
    tokenizer.reset(metatokens)
    # create full function name tokens
    metatokens = tokenizer.match_patterns()
    tokenizer.reset(metatokens)
    # create paths to reduce the number of tokens
    metatokens = tokenizer.make_paths()
    tokenizer.reset(metatokens)
    # split on unused meta tokens
    tokens = tokenizer.split()

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
  tokenize(conn)

if __name__ == "__main__":
   main(sys.argv[1:])