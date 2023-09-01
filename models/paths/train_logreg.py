import sqlite3, sys, os, getopt, pandas as pd
from datetime import datetime
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from joblib import dump
from utils import PathsClassifierUtils as utils


HELP = 'Usage:\npython train_logreg.py --dbpath="<database path>"\n'
MODEL_FILE = 'paths_logreg.joblib'
COLUMNS = ['ref_depth',
           'is_upward',
           'nb_referrers',
           'nb_strings',
           'nb_referees',
           'instructions',
           'lit_vec']
"""Training data features."""

def train_logistic_regression(conn: sqlite3.Connection):
  """Trains cross-reference path Logistic Regression classifier (scikit-learn) and saves it to a file."""
  cur = conn.cursor()
  start = datetime.now()

  print('Loading FastText model...')
  try:
    ft = utils.load_ft(utils.get_embedder_path())
  except Exception as ex:
    print(ex)
    sys.exit()

  print("Fetching data...")
  data = utils.get_unbalanced_data(cur)
  labels = data['names_func']
  data.drop(['names_func'], axis=1, inplace=True)
  
  print("Performing word embedding...")
  data = utils.ft_embed(ft, data)
  data.drop(['token_literal'], axis=1, inplace=True)

  print('Initializing classifier model...')
  # max_iter doubled due to training warnings:
  # ConvergenceWarning: lbfgs failed to converge
  lr = LogisticRegression(max_iter=200, random_state=0)

  print("Splitting datasets...")
  x_train, _, y_train, _ = utils.split_dataset(data, labels)
  x_train = pd.DataFrame(data=x_train, columns=COLUMNS)
  x_train = utils.listify(x_train)
  y_train = tuple(y_train.to_list())

  print("Scaling data...")
  scaler = StandardScaler()
  scaler.fit(x_train)
  scaler.transform(x_train)

  print("Cross-validation (5-fold)...")
  scores = cross_val_score(lr, X=x_train, y=y_train, scoring='f1')
  print("F1: %0.3f" % (scores.mean()))
  print("Std_dev: %0.3f" % (scores.std()))

  print("Training classifier...")
  lr.fit(X=x_train, y=y_train)
  file_path = utils.get_model_path(MODEL_FILE)
  dump(lr, file_path)
  print(f'Model saved to {file_path}')
  print(f'Start time:\t{start}')
  print(f'End time:\t{datetime.now()}')

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
  train_logistic_regression(conn)
  conn.close()

if __name__ == "__main__":
  main(sys.argv[1:])
