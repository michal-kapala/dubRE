import os, sys, getopt
import sqlite3, json
from io import TextIOWrapper
from datetime import datetime
from utils.db import DbException


HELP = 'Usage:\npython mergedb.py --config=<JSON file path>\n'

def add_db(in_cur: sqlite3.Cursor, out_conn: sqlite3.Connection, label: str):
  """Adds one database to the dataset."""
  out_cur = out_conn.cursor()

  pdb_funcs = []
  funcs = []
  strings = []
  tokens = []
  paths =[]
  tpaths = []

  # Query the data (includes unlabelled samples)

  try:
    in_cur.execute("SELECT * FROM pdb")
    pdb_funcs = in_cur.fetchall()
  except Exception as ex:
    print(ex)
    sys.exit()

  try:
    in_cur.execute("SELECT * FROM funcs")
    funcs = in_cur.fetchall()
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

  try:
    in_cur.execute("SELECT * FROM paths")
    paths = in_cur.fetchall()
  except Exception as ex:
    print(ex)
    sys.exit()

  try:
    in_cur.execute("SELECT * FROM token_paths")
    tpaths = in_cur.fetchall()
  except Exception as ex:
    print(ex)
    sys.exit()

  # Insert the data with transformed primary keys

  for pdbf in pdb_funcs:
    try:
      # binary name column added
      out_cur.execute(
        "INSERT INTO pdb VALUES (?,?,?,?)", (label, pdbf[0], pdbf[1], pdbf[2])
      )
    except Exception as ex:
      print(ex)
      break
    
  print(f"Merged `pdb` of {label}")
    
  for func in funcs:
    try:
      # id column swapped out for binary name
      out_cur.execute(
        "INSERT INTO funcs VALUES (?,?,?,?,?,?)", (label, func[1], func[2], func[3], func[4], func[5])
      )
    except Exception as ex:
      print(ex)
      break
    
  print(f"Merged `funcs` of {label}")
    
  for string in strings:
    try:
      # binary name column added
      out_cur.execute(
        "INSERT INTO strings VALUES (?,?,?)", (label, string[0], string[1])
      )
    except Exception as ex:
      print(ex)
      break
    
  print(f"Merged `strings` of {label}")
    
  for tkn in tokens:
    # skip unlabelled tokens
    # if tkn[2] is None:
    #   continue
    try:
      # binary name column added
      out_cur.execute(
        "INSERT INTO tokens VALUES (?,?,?,?)", (label, tkn[0], tkn[1], tkn[2])
      )
    except Exception as ex:
      print(ex)
      break
  
  print(f"Merged `tokens` of {label}")
    
  for path in paths:
    try:
      # (global) id added (autoincremented primary key)
      # binary name added
      # id renamed to local_id (unique in a binary)
      out_cur.execute(
        "INSERT INTO paths (binary,local_id,func_addr,string_addr,path_func1,path_func2,path_func3,ref_depth,is_upward,to_name) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (label, path[0], path[1], path[2], path[3], path[4], path[5], path[6], path[7], path[8])
      )
    except Exception as ex:
      print(ex)
      break
    
  print(f"Merged `paths` of {label}")
    
  for tpath in tpaths:
    try:
      # binary name added
      # path_id renamed to local_path_id (unique in a binary)
      # the primary key is binary + local_path_id + token_literal
      out_cur.execute(
        "INSERT INTO token_paths VALUES (?,?,?,?,?,?)",
        (label, tpath[0], tpath[1], tpath[2], tpath[3], tpath[4])
      )
    except Exception as ex:
      print(ex)
      break

  print(f"Merged `token_paths` of {label}")

def merge_db(config_file: TextIOWrapper):
  """Merges single-binary databases into one dataset."""
  
  print(f"start:\t{datetime.now()}")

  config = json.load(config_file)
  output_file = config["outputFile"]
  files = config["files"]

  output_conn = sqlite3.connect(output_file)
  output_cur = output_conn.cursor()
  output_cur.execute('''CREATE TABLE IF NOT EXISTS pdb (
              binary TEXT NOT NULL,
              func_addr INTEGER NOT NULL,
              literal TEXT,
              demangled INTEGER NOT NULL,
              PRIMARY KEY (binary, func_addr))''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS funcs (
              binary TEXT NOT NULL,
              func_addr INTEGER NOT NULL,
              nb_referrers INTEGER NOT NULL,
              nb_strings INTEGER NOT NULL,
              nb_referees INTEGER NOT NULL,
              instructions INTEGER NOT NULL,
              PRIMARY KEY (binary, func_addr))''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS strings (
              binary TEXT NOT NULL,
              address INTEGER NOT NULL,
              literal TEXT NOT NULL,
              PRIMARY KEY (binary, address))''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS tokens (
              binary TEXT NOT NULL,
              string_addr INTEGER NOT NULL,
              literal TEXT NOT NULL,
              is_name INTEGER)''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS paths (
              id INTEGER PRIMARY KEY,
              binary TEXT NOT NULL,
              local_id INTEGER NOT NULL,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              path_func1 INTEGER NOT NULL,
              path_func2 INTEGER NOT NULL,
              path_func3 INTEGER NOT NULL,
              ref_depth INTEGER NOT NULL,
              is_upward INTEGER NOT NULL,
              to_name INTEGER,
              UNIQUE (binary, func_addr, string_addr, path_func1, path_func2, path_func3))''')
  
  output_cur.execute('''CREATE TABLE IF NOT EXISTS token_paths (
              binary TEXT NOT NULL,
              local_path_id INTEGER NOT NULL,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              token_literal TEXT NOT NULL,
              names_func INTEGER)''')
  
  output_conn.commit()
  print(f"Tables created")

  for file in files:
    label = file["label"]
    input_path = file["path"]

    if not os.path.isfile(input_path):
      raise DbException(f"Input database not found at {input_path}")

    input_conn = sqlite3.connect(input_path)
    input_cur = input_conn.cursor()

    add_db(input_cur, output_conn, label)
    input_conn.close()
    output_conn.commit()
    print(f"Committed {label}")

  output_conn.close()
  print(f"end:\t{datetime.now()}")


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
