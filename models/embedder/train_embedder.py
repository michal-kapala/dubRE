import sqlite3, sys, os, getopt, pandas as pd
from gensim.models import FastText


HELP = 'Usage:\npython train_embedder.py --dbpath="<database path>"\n'
COLUMNS = ['binary', 'string_addr', 'literal', 'is_name']

def train_ft(data: list[list[str]]) -> FastText:
  """Trains FastText model from a token list."""
  return FastText(sentences=data, vector_size=1, window=3, min_count=1)

def save_ft(model: FastText):
  """Saves FastText model to a file."""
  model.save('embedder.ft')

def load_ft(path: str) -> FastText:
  """Loads a pretrained FastText model from a file."""
  return FastText.load(path)

def listify(lst: list[str]) -> list[list[str]]:
  """Transforms `list[str]` into a `list[list[str]]`."""
  result = []
  for elem in lst:
    result.append([elem])
  return result

def train_token_embedder(conn: sqlite3.Connection):
  """Trains text feature (token) embedding model (FastText) and saves it to a file."""
  cur = conn.cursor()

  try:
    cur.execute('SELECT * FROM tokens WHERE is_name IS NOT NULL')
    tokens = cur.fetchall()
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  tokens = pd.DataFrame(data=tokens, columns=COLUMNS)['literal']

  # FastText 'sentences' (one word-long)
  ft_data = listify(tokens.to_list())
  print('Training FastText embedder...')
  ft = train_ft(ft_data)
  save_ft(ft)
  print('Training finished, saved FastText model to `embedder.ft`')
  # X_train, X_test, y_train, y_test = train_test_split(df, test_size=0.1, random_state=0)
  

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
    raise Exception(f"SQLite database path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise Exception(f"Database not found at {db_path}")
  
  conn = sqlite3.connect(db_path)
  train_token_embedder(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])