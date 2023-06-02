import os, sys, getopt
import sqlite3, json
from io import TextIOWrapper
from datetime import datetime
from utils.db import DbException
from demangler.demangler import Demangler


HELP = 'Usage:\npython pdb.py -d <database path> -j <JSON file path>\n'

def process_pdb(conn: sqlite3.Connection, file: TextIOWrapper):
  """Demangles and saves PDB functions in the database."""
  
  print(f"start:\t{datetime.now()}")
  c = conn.cursor()
  c.execute('''CREATE TABLE IF NOT EXISTS pdb
              (func_addr integer NOT NULL, literal text UNIQUE, demangled integer NOT NULL)''')
  
  pdb = json.load(file)
  
  for func in range(len(pdb)):
    name = pdb[func]["name"]

    # irrelevant function
    if "`" in name or "'" in name or "<lambda_" in name or "<unnamed-type-" in name:
      continue
    
    demangled = 1
    if name[0] == "?":
      name = Demangler.process_mangled(name)

      # ignored special name
      if name == "":
        continue

      pdb[func]["name"] = name
    else:
      name = Demangler.process_unmangled(name)
      pdb[func]["name"] = name
      demangled = 0

    try:
      c.execute("INSERT INTO pdb VALUES (?,?,?)", (pdb[func]["address"], name, demangled))
    # Skip duplicate errors on UNIQUE db constraint ('UNIQUE constraint failed: pdb.literal')
    except sqlite3.IntegrityError:
      pass
    except Exception as ex:
      print(ex)
      break

  print(f"end:\t{datetime.now()}")


def main(argv):
  db_path = ""
  file_path = ""
  opts, args = getopt.getopt(argv,"hdj:",["dbpath=", "json="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-j", "--json"):
      file_path = arg

  if db_path == "":
    raise DbException(f"SQLite database path required\n{HELP}")
  if file_path == "":
    raise DbException(f"PDB JSON file path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise DbException(f"Database not found at {db_path}")
  if not os.path.isfile(file_path):
    raise DbException(f"JSON file not found at {file_path}")

  conn = sqlite3.connect(db_path)
  file = open(file_path)
  
  process_pdb(conn, file)

  file.close()
  conn.commit()
  conn.close()
  

if __name__ == "__main__":
   main(sys.argv[1:])
