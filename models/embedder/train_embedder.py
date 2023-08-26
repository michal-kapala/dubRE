import sqlite3, sys, os, getopt, pandas as pd
from gensim.models import FastText
from sklearn.model_selection import train_test_split


HELP = 'Usage:\npython train_embedder.py --dbpath="<database path>"\n'
COLUMNS = ['literal', 'is_name']
TEST_SIZE_RATIO = 0.2
"""Desired percentage of test samples in the dataset."""

def train_ft(data: list[list[str]]) -> FastText:
  """Trains FastText model from a token list."""
  return FastText(sentences=data, vector_size=1, window=3, min_count=1)

def save_ft(model: FastText):
  """Saves FastText model to a file."""
  model.save('embedder.ft')

def balance_dataset(tokens_df: pd.DataFrame, pdb_df: pd.DataFrame) -> pd.DataFrame:
  """Returns a complete dataset balanced with PDB positives."""
  # calculate the nb of missing positives
  nb_neg = tokens_df[tokens_df['is_name'] == 0].shape[0]
  nb_pos = tokens_df.shape[0] - nb_neg
  nb_missing_pos = nb_neg - nb_pos

  # deterministic shuffle
  balancing_pos, _ = train_test_split(pdb_df, train_size=nb_missing_pos, random_state=0)
  return pd.concat([tokens_df, balancing_pos], ignore_index=True)

def train_token_embedder(conn: sqlite3.Connection):
  """Trains text feature (token) embedding model (FastText) and saves it to a file."""
  cur = conn.cursor()

  # query binary-native tokens
  try:
    cur.execute('SELECT literal, is_name FROM tokens WHERE is_name IS NOT NULL')
    tokens = cur.fetchall()
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  # query function name positives from pdb to balance the dataset
  try:
    cur.execute('SELECT literal FROM pdb')
    pdb = cur.fetchall()
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  pdb_df = pd.DataFrame(data=pdb, columns=['literal'], index=range(len(pdb)))
  pdb_df['is_name'] = ''
  
  for idx in pdb_df.index:
    pdb_df.at[idx, 'is_name'] = 1

  df = pd.DataFrame(data=tokens, columns=COLUMNS)
  df = balance_dataset(df, pdb_df)

  # deterministic shuffle, the same splitting is used for classifier datasets
  train, _ = train_test_split(df, test_size=TEST_SIZE_RATIO, random_state=0)
  ft_data = train.drop(['is_name'], axis=1).values.tolist()
  print(train)

  # FastText 'sentences' (one word-long)
  print('Training FastText embedder...')
  ft = train_ft(ft_data)
  save_ft(ft)
  print('Training finished, saved FastText model to `embedder.ft`')

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