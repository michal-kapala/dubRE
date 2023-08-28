import sqlite3, sys, os, getopt, pandas as pd
from datetime import datetime
from sklearn.metrics import confusion_matrix
from sklearn.preprocessing import StandardScaler
from joblib import load
from utils import NameClassifierUtils as utils


HELP = 'Usage:\npython test.py --dbpath="<dataset db path>" --results"<results db path>" --model="<model filename>"\n'
ITERS = 10
"""Number of testing iterations (predictions made on different sample sets). Data shuffling used is reproducible."""

def test_model(conn: sqlite3.Connection, results_path: str, model: str):
  """Tests function name classifier model of choice and saves the results."""
  cur = conn.cursor()
  start = datetime.now()

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
  _, x_test, _, y_test = utils.split_dataset(literals, labels)
  
  print("Performing word embedding...")
  x_test = pd.DataFrame(data=x_test, columns = ['literal'])
  x_test = utils.ft_embed(ft, x_test)
  X_test = utils.listify(x_test['lit_vec'].to_list())
  y_test = tuple(y_test.to_list())

  # scaling
  scaler = StandardScaler()
  scaler.fit(X_test)
  scaler.transform(X_test)

  print('Loading classifier model...')
  file_path = utils.get_model_path(model)
  try:
    clf = load(file_path)
  except Exception as ex:
    print(ex)
    sys.exit()

  print("Predicting...")
  y_pred = clf.predict(X=X_test)
  
  # stats
  tn, fp, fn, tp = confusion_matrix(y_test, y_pred, labels=[0, 1]).ravel()
  pos = tp + fn 
  neg = tn + fp
  accuracy = (tp + tn) / (pos + neg)
  precision = tp / (tp + fp)
  recall = tp / pos

  if pos + neg == 0:
    print(f"Why are you testing with no data?")
    sys.exit()
  accuracy = (tp + tn) / (pos + neg)

  if tp + fp == 0:
    print("Precision could not be calculated (no positive predictions)")
    precision = None
  else:
    precision = tp / (tp + fp)

  if pos == 0:
    print("Recall could not be calculated - why are you testing with no positive samples in the set?")
    recall = None
  else:
    recall = tp / pos

  if precision == 0 or recall == 0:
    f1 = 0
  elif precision is None or recall is None:
    f1 = None
  else:
    f1 = 2 * precision * recall / (precision + recall)
  
  print(f"Accuracy: {accuracy * 100:.3f}%")
  results = {
    "pos": pos,
    "neg": neg,
    "tp": tp,
    "tn": tn,
    "fp": fp,
    "fn": fn,
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1
  }
  
  table = model.replace('.joblib', '')
  utils.save_results(results, table, results_path)

  print(f'Start time:\t{start}')
  print(f'End time:\t{datetime.now()}')

def main(argv):
  db_path = ""
  results_path = ""
  opts, _ = getopt.getopt(argv,"hdr:",["dbpath=", "results=", "model="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-r", "--results"):
      results_path = arg
    elif opt in ("-m", "--model"):
      model = arg

  if db_path == "":
    raise Exception(f"Dataset SQLite database path required\n{HELP}")
  if results_path == "":
    raise Exception(f"Results SQLite database path required\n{HELP}")
  if model == "":
    raise Exception(f"Model file name (with extension) required\n{HELP}")
  
  if not os.path.isfile(db_path):
    raise Exception(f"Dataset database not found at {db_path}")
  
  if not os.path.isfile(results_path):
    raise Exception(f"Results database not found at {results_path}")
  
  model_path = utils.get_model_path(model)
  if not os.path.isfile(model_path):
    raise Exception(f"Model not found at {model_path}")
  
  conn = sqlite3.connect(db_path)
  test_model(conn, results_path, model)
  conn.close()
  

if __name__ == "__main__":
  main(sys.argv[1:])