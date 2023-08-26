import sqlite3, sys, os, getopt, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB
from gensim.models import FastText


HELP = 'Usage:\npython train_nbayes.py --dbpath="<database path>"\n'
COLUMNS = ['binary', 'string_addr', 'literal', 'is_name']

def get_embedder_path():
  """Returns the path to FastText model file."""
  models_path, _ = os.path.split(os.getcwd())
  return os.path.join(models_path, 'embedder\\embedder.ft')

def load_ft(path: str) -> FastText:
  """Loads a pretrained FastText model from a file."""
  return FastText.load(path)

def train_naive_bayes(conn: sqlite3.Connection):
  """Trains function name classifier using Naive Bayes (scikit-learn) model and saves it to a file."""
  cur = conn.cursor()

  try:
    cur.execute('SELECT * FROM tokens WHERE is_name IS NOT NULL')
    tokens = cur.fetchall()
  # 'no such table: x'
  except sqlite3.OperationalError as ex:
    print(ex)
    sys.exit()

  df = pd.DataFrame(data=tokens, columns=COLUMNS)
  tokens = df['literal']
  labels = df['is_name']
  try:
    # load FastText text embedder (Windows paths only!)
    ft = load_ft(get_embedder_path())
  except Exception as ex:
    print(ex)
    sys.exit()
  print(ft.wv['std::cout'])
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
  train_naive_bayes(conn)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])