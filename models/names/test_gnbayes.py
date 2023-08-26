import sqlite3, sys, os, getopt, pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score
from joblib import load
from utils import NameClassifierUtils as utils


HELP = 'Usage:\npython test_gnbayes.py --dbpath="<dataset db path>" --results"<results db path>"\n'
MODEL_FILE = 'names_gnbayes.joblib'

def test_naive_bayes(conn: sqlite3.Connection, results_path: str):
  """Tests Gaussian Naive Bayes (scikit-learn) function name classifier and saves the results."""
  cur = conn.cursor()
  print("Fetching data...")
  tokens = utils.query_tokens(cur)
  pdb = utils.query_pdb(cur)
  df = utils.balance_dataset(tokens, pdb)
  print('Loading FastText model...')
  try:
    ft = utils.load_ft(utils.get_embedder_path())
  except Exception as ex:
    print(ex)
    sys.exit()
  literals = df['literal']
  labels = df['is_name']

  print("Splitting datasets...")
  x_train, x_test, y_train, y_test = utils.split_dataset(literals, labels)
  
  print("Performing word embedding...")
  x_test = pd.DataFrame(data=x_test, columns = ['literal'])
  x_test = utils.ft_embed(ft, x_test)
  X_test = utils.listify(x_test['lit_vec'].to_list())
  y_test = tuple(y_test.to_list())

  # scaling
  scaler = StandardScaler()
  scaler.fit(X_test)
  scaler.transform(X_test)

  file_path = utils.get_model_path(MODEL_FILE)
  print('Loading classifier model...')
  try:
    gnb = load(file_path)
  except Exception as ex:
    print(ex)
    sys.exit()

  print("Predicting...")
  y_pred = gnb.predict(X=X_test)
  print(y_pred)
  print("Number of mislabeled points out of a total %d points : %d" % (x_test.shape[0], (y_test != y_pred).sum()))

  # structure and save results
  table = MODEL_FILE.replace('.joblib', '')

  x_test['label'] = ''
  x_test['prediction'] = ''
  x_test = x_test.reset_index(drop=True)
  for idx in x_test.index:
    x_test.at[idx, 'label'] = y_test[idx]
    x_test.at[idx, 'prediction'] = y_pred[idx]
  
  print(x_test)
  utils.save_results(x_test, table, results_path)

def main(argv):
  db_path = ""
  results_path = ""
  opts, args = getopt.getopt(argv,"hdr:",["dbpath=", "results="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-r", "--results"):
      results_path = arg

  if db_path == "":
    raise Exception(f"Dataset SQLite database path required\n{HELP}")
  if results_path == "":
    raise Exception(f"Results SQLite database path required\n{HELP}")
  if not os.path.isfile(db_path):
    raise Exception(f"Dataset database not found at {db_path}")
  if not os.path.isfile(results_path):
    raise Exception(f"Dataset database not found at {results_path}")
  
  conn = sqlite3.connect(db_path)
  test_naive_bayes(conn, results_path)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])