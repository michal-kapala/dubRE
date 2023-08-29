import os, sys, getopt
import sqlite3
from datetime import datetime
from joblib import load
from sklearn.preprocessing import StandardScaler
from utils import PipelineUtils as utils


HELP = 'Usage:\npython test_pipeline.py --dbpath="<dataset path>" --results="<results db path>" --names="<names classifier model file> --paths="<paths classifier model file>"\n'

def test_pipeline(conn: sqlite3.Connection, results_path: str, names_model_file: str, paths_model_file: str):
  """Simulates a plugin scenario and evaluates common predictions of both classifiers."""
  cur = conn.cursor()
  start = datetime.now()

  print('Loading FastText model...')
  try:
    ft = utils.load_ft(utils.get_embedder_path())
  except Exception as ex:
    print(ex)
    sys.exit()

  print("Fetching data...")
  data = utils.query_data(cur)
  data['lit_vec'] = ''
  
  print("Performing word embedding...")
  data = utils.ft_embed(ft, data)
  data.drop(['token_literal'], axis=1, inplace=True)
    
  print('Loading classifier models...')
  try:
    names_clf = load(utils.get_model_path(names_model_file))
    paths_clf = load(utils.get_model_path(paths_model_file))
  except Exception as ex:
    print(ex)
    sys.exit()

  names = utils.listify_names(data['lit_vec'].to_list())
  print("Scaling names data...")
  scaler = StandardScaler()
  scaler.fit(names)
  scaler.transform(names)

  print("Predicting names...")
  data['name_pred'] = names_clf.predict(X=names)

  # rearrange columns
  paths = data.drop(['binary', 'func_addr', 'names_func', 'name_pred'], axis=1)
  paths = paths[['ref_depth',
           'is_upward',
           'nb_referrers',
           'nb_strings',
           'nb_referees',
           'instructions',
           'lit_vec']]
  paths = utils.listify_paths(paths)

  print(f"Scaling paths...")
  scaler = StandardScaler()
  scaler.fit(paths)
  scaler.transform(paths)
  
  print("Predicting paths...")
  data['path_pred'] = paths_clf.predict(paths)
  path_prob = paths_clf.predict_proba(paths)
  data['path_pred_prob1'] = ''

  for idx in data.index:
    data.at[idx, 'path_pred_prob1'] = path_prob[idx][1]

  funcs = utils.group_in_funcs(data)

  # stats
  tp = 0
  tn = 0
  fp = 0
  fn = 0

  for func in funcs:
    for tpath in func:
      truth = tpath[4]
      names_pred = tpath[10]
      paths_pred = tpath[11]
      if truth == 0 and names_pred == 0:
        tn += 1
      if truth == 1 and names_pred == 0:
        fn += 1
      if truth == 1 and names_pred == 1 and paths_pred == 1:
        tp += 1
      if truth == 1 and names_pred == 1 and paths_pred == 0:
        fn += 1
      if truth == 0 and names_pred == 1 and paths_pred == 0:
        tn += 1
      if truth == 0 and names_pred == 1 and paths_pred == 1:
        fp += 1


  if tp + tn + fp + fn == 0:
    print(f"Why are you testing with no data?")
    sys.exit()

  accuracy = (tp + tn) / (tp + tn + fp + fn)

  if tp + fp == 0:
    print("Precision could not be calculated (no positive predictions)")
    precision = None
  else:
    precision = tp / (tp + fp)

  if tp + fn == 0:
    print("Recall could not be calculated - why are you testing with no positive samples in the set?")
    recall = None
  else:
    recall = tp / (tp + fn)

  if precision is None or recall is None:
    f1 = None
  else:
    if precision == 0 or recall == 0:
      f1 = 0
    else:
      f1 = 2 * precision * recall / (precision + recall)

  print(f"Accuracy: {accuracy * 100:.3f}%")
  results = {
    "pos": tp + fn,
    "neg": tn + fp,
    "tp": tp,
    "tn": tn,
    "fp": fp,
    "fn": fn,
    "accuracy": accuracy,
    "precision": precision,
    "recall": recall,
    "f1": f1
  }
  print(results)

  names_clf_name = names_model_file.replace('names_', '').replace('.joblib', '')
  paths_clf_name = paths_model_file.replace('paths_', '').replace('.joblib', '')
  table = f"pipe_{names_clf_name}_{paths_clf_name}"
  utils.save_results(results, table, results_path)
      

  print(f'Start time:\t{start}')
  print(f'End time:\t{datetime.now()}')


def main(argv):
  db_path = ""
  results_path = ""
  names_model = ""
  paths_model = ""
  opts, _ = getopt.getopt(argv,"hdrnp:",["dbpath=", "results=", "names=", "paths="])
  for opt, arg in opts:
    if opt == '-h':
      print(HELP)
      sys.exit()
    elif opt in ("-d", "--dbpath"):
      db_path = arg
    elif opt in ("-r", "--results"):
      results_path = arg
    elif opt in ("-n", "--names"):
      names_model = arg
    elif opt in ("-p", "--paths"):
      paths_model = arg

  if db_path == "":
    raise Exception(f"Dataset SQLite database path required\n{HELP}")
  if results_path == "":
    raise Exception(f"Results SQLite database path required\n{HELP}")
  if names_model == "":
    raise Exception(f"Function name model file name (with extension) required\n{HELP}")
  if paths_model == "":
    raise Exception(f"Xref paths model file name (with extension) required\n{HELP}")
  
  if not os.path.isfile(db_path):
    raise Exception(f"Dataset database not found at {db_path}")
  
  if not os.path.isfile(results_path):
    raise Exception(f"Results database not found at {results_path}")
  
  names_model_path = utils.get_model_path(names_model)
  if not os.path.isfile(names_model_path):
    raise Exception(f"Function name model not found at {names_model_path}")
  
  paths_model_path = utils.get_model_path(paths_model)
  if not os.path.isfile(paths_model_path):
    raise Exception(f"Xref path model not found at {paths_model_path}")

  conn = sqlite3.connect(db_path)
  
  test_pipeline(conn, results_path, names_model, paths_model)

  conn.commit()
  conn.close()
  
if __name__ == "__main__":
   main(sys.argv[1:])
