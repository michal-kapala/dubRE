import sqlite3, sys, os, getopt, pandas as pd
from sklearn.svm import LinearSVC
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from joblib import dump
from utils import NameClassifierUtils as utils


HELP = 'Usage:\npython train_lsvc.py --dbpath="<database path>"\n'
MODEL_FILE = 'names_lsvc.joblib'

def train_linear_svc(conn: sqlite3.Connection):
  """Trains function name classifier using Linear Support Vector model (scikit-learn) and saves it to a file."""
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
  svc = LinearSVC(dual='auto', random_state=0)

  print("Cross-validation (5-fold)...")
  scores = cross_val_score(svc, X=x_train, y=y_train)
  print("Accuracy: %0.3f" % (scores.mean()))
  print("Std_dev: %0.3f" % (scores.std()))

  print("Training classifier...")
  svc.fit(X=x_train, y=y_train)
  file_path = utils.get_model_path(MODEL_FILE)
  dump(svc, file_path)
  print(f'Model saved to {file_path}')

def main(argv):
  db_path = ""
  opts, _ = getopt.getopt(argv,"hd:",["dbpath="])
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
  train_linear_svc(conn)
  conn.close()
  
if __name__ == "__main__":
  main(sys.argv[1:])
