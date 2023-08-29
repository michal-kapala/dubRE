import os, sys, getopt
import sqlite3
from datetime import datetime
from sklearn.model_selection import train_test_split
from utils import PipelineUtils as utils


HELP = 'Usage:\npython seen_tokens.py --dbpath="<dataset path>"\n'

def count_seen_tokens(conn: sqlite3.Connection):
  """Calculates the percentage of pipeline data seen by function name classifiers during training."""
  cur = conn.cursor()
  start = datetime.now()

  print("Fetching data...")
  data = utils.query_data(cur)

  tokens = utils.query_tokens(cur)
  pdb = utils.query_pdb(cur)
  train_tokens = utils.balance_dataset(tokens, pdb)
  train_tokens = train_tokens['literal']

  print("Splitting tokens dataset...")
  x_train, _ = utils.split_dataset(train_tokens)
  x_train = x_train.to_list()
  seen_tokens = 0

  print("Counting...")
  for idx in data.index:
    print(idx)
    if data.at[idx, 'token_literal'] in x_train:
      seen_tokens += 1

  percent_seen = seen_tokens / data.shape[0] * 100
  print(f"Percentage of tokens seen during training present in test set is {percent_seen:.3f}%")
      
  print(f'Start time:\t{start}')
  print(f'End time:\t{datetime.now()}')

def main(argv):
  db_path = ""
  opts, _ = getopt.getopt(argv,"hdrnp:",["dbpath=", "results="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg

  if db_path == "":
    raise Exception(f"Dataset SQLite database path required\n{HELP}")
  
  if not os.path.isfile(db_path):
    raise Exception(f"Dataset database not found at {db_path}")  

  conn = sqlite3.connect(db_path)
  
  count_seen_tokens(conn)

  conn.commit()
  conn.close()
  
if __name__ == "__main__":
   main(sys.argv[1:])
