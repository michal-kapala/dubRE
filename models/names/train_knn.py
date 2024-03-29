import sqlite3, sys, os, getopt, pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from joblib import dump
from utils import NameClassifierUtils as utils


HELP = 'Usage:\npython train_knn.py --dbpath="<database path> --k=<k neighbors parameter>"\n'
MODEL_FILE = 'names_@knn.joblib'

def train_nearest_neighbours(conn: sqlite3.Connection, k: int):
  """Trains function name classifier using k-Nearest Neighbors model (scikit-learn) and saves it to a file."""
  cur = conn.cursor()

  print('Loading FastText model...')
  try:
    ft = utils.load_ft(utils.get_embedder_path())
  except Exception as ex:
    print(ex)
    sys.exit()

  print("Fetching data...")
  tokens = utils.query_tokens(cur)
  pdb = utils.query_pdb(cur)
  df = utils.balance_dataset(tokens, pdb)
  
  literals = df['literal']
  labels = df['is_name']

  print("Splitting datasets...")
  x_train, _, y_train, _ = utils.split_dataset(literals, labels)
  
  print("Performing word embedding...")
  x_train = pd.DataFrame(data=x_train, columns = ['literal'])
  x_train = utils.ft_embed(ft, x_train)
  x_train = utils.listify(x_train['lit_vec'].to_list())
  y_train = tuple(y_train.to_list())

  print("Scaling data...")
  scaler = StandardScaler()
  scaler.fit(x_train)
  scaler.transform(x_train)

  print('Initializing classifier model...')
  # 5 neighbors is the default
  knn = KNeighborsClassifier(n_neighbors=k)

  print("Cross-validation (5-fold)...")
  scores = cross_val_score(knn, X=x_train, y=y_train)
  print("Accuracy: %0.3f" % (scores.mean()))
  print("Std_dev: %0.3f" % (scores.std()))

  print("Training classifier...")
  knn.fit(X=x_train, y=y_train)
  file_path = utils.get_model_path(MODEL_FILE.replace("@", str(k)))
  dump(knn, file_path)
  print(f'Model saved to {file_path}')

def main(argv):
  db_path = ""
  k = 0
  opts, _ = getopt.getopt(argv,"hdk:",["dbpath=", "k="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-k", "--k"):
      try:
        k = int(arg)
      except Exception as ex:
        print("Invalid k parameter supplied")
        sys.exit()

  if db_path == "":
    raise Exception(f"SQLite database path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise Exception(f"Database not found at {db_path}")
  if k < 1 or k > 10:
    raise Exception("The allowed range for k parameter is [1,10]")
  
  conn = sqlite3.connect(db_path)
  train_nearest_neighbours(conn, k)
  conn.close()
  
if __name__ == "__main__":
  main(sys.argv[1:])
