import os, sys, getopt
import sqlite3, json
from io import TextIOWrapper
from datetime import datetime
from utils.db import DbException


HELP = 'Usage:\npython mergedb.py --config=<JSON file path>\n'

def add_db(in_cur: sqlite3.Cursor, out_cur: sqlite3.Cursor, label: str):
  """Adds one database to the dataset."""
  pdb_funcs = []
  strings = []
  tokens = []

  try:
    in_cur.execute("SELECT * FROM pdb")
    pdb_funcs = in_cur.fetchall()
  except Exception as ex:
    print(ex)
    sys.exit()

  try:
    in_cur.execute("SELECT * FROM strings")
    strings = in_cur.fetchall()
  except Exception as ex:
    print(ex)
    sys.exit()
  
  try:
    in_cur.execute("SELECT * FROM tokens")
    tokens = in_cur.fetchall()
  except Exception as ex:
    print(ex)
    sys.exit()

  for func in pdb_funcs:
    try:
      out_cur.execute(
        "INSERT INTO pdb VALUES (?,?,?,?)", (label, func[0], func[1], func[2])
      )
    except Exception as ex:
        print(ex)
        break
    
  for string in strings:
    try:
      out_cur.execute(
        "INSERT INTO strings VALUES (?,?,?)", (label, string[0], string[1])
      )
    except Exception as ex:
        print(ex)
        break
    
  for tkn in tokens:
    # skip unlabelled tokens
    if tkn[2] is None:
      continue
    try:
      out_cur.execute(
        "INSERT INTO tokens VALUES (?,?,?,?)", (label, tkn[0], tkn[1], tkn[2])
      )
    except Exception as ex:
        print(ex)
        break

  print(f"Merged {label}")

def merge_db(config_file: TextIOWrapper):
  """Merges single-binary databases into one dataset."""
  
  print(f"start:\t{datetime.now()}")

  config = json.load(config_file)
  output_file = config["outputFile"]
  files = config["files"]

  output_conn = sqlite3.connect(output_file)
  output_cur = output_conn.cursor()
  output_cur.execute('''CREATE TABLE IF NOT EXISTS pdb
              (binary text NOT NULL, func_addr integer NOT NULL, literal text, demangled integer NOT NULL)''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS strings
                (binary text NOT NULL, address integer NOT NULL, literal text)''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS tokens
              (binary text NOT NULL, string_addr integer NOT NULL, literal text, is_name integer NOT NULL)''')

  for file in files:
    label = file["label"]
    input_path = file["path"]

    if not os.path.isfile(input_path):
      raise DbException(f"Input database not found at {input_path}")

    input_conn = sqlite3.connect(input_path)
    input_cur = input_conn.cursor()

    add_db(input_cur, output_cur, label)

    input_conn.close()

  print(f"end:\t{datetime.now()}")

  output_conn.commit()
  output_conn.close()


def main(argv):
  config_path = ""
  opts, args = getopt.getopt(argv,"hc:",["config="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-c", "--config"):
      config_path = arg

  if config_path == "":
    raise DbException(f"Config JSON file path required\n{HELP}")
  if not os.path.isfile(config_path):
    raise DbException(f"Config JSON file not found at {config_path}")
  
  config_file = open(config_path)
  merge_db(config_file)
  config_file.close()
  

if __name__ == "__main__":
   main(sys.argv[1:])
