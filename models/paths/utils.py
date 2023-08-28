import sqlite3, sys, os, pandas as pd
from gensim.models import FastText
from sklearn.model_selection import train_test_split

_COLUMNS = [
  'token_literal',
  'names_func',
  'ref_depth',
  'is_upward',
  'nb_referrers',
  'nb_strings',
  'nb_referees',
  'instructions'
  ]
_TEST_SIZE_RATIO = 0.2
"""Desired percentage of test samples in the dataset."""

class PathsClassifierUtils:
  """Utility functions for cross-reference paths classifiers."""
  @staticmethod
  def get_balanced_data(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns all positive-labeled token paths with balancing number of negatives, enriched with path and function features."""
    try:
      # small query
      cur.execute('SELECT binary, local_path_id, func_addr, token_literal, names_func FROM token_paths WHERE names_func = 1')
      tpaths_pos = cur.fetchall()
      # big query - to be shuffled and split
      cur.execute('SELECT binary, local_path_id, func_addr, token_literal, names_func FROM token_paths WHERE names_func = 0')
      tpaths_neg_all = cur.fetchall()
      # big query - overfetching once is faster than fetching N times
      cur.execute('SELECT binary, local_id, ref_depth, is_upward FROM paths WHERE to_name IS NOT NULL')
      paths = cur.fetchall()
      # big query - overfetching once is faster than fetching N times
      cur.execute('SELECT binary, func_addr, nb_referrers, nb_strings, nb_referees, instructions FROM funcs')
      func_data = cur.fetchall()
    # 'no such table: x'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

    print("Structuring data...")
    # deterministic shuffle
    tpaths_neg, _ = train_test_split(tpaths_neg_all, train_size=len(tpaths_pos), random_state=0)
    tpaths = tpaths_pos + tpaths_neg
    df = pd.DataFrame(data=tpaths, columns=_COLUMNS)
    df['ref_depth'] = ''
    df['is_upward'] = ''
    df['nb_referrers'] = ''
    df['nb_strings'] = ''
    df['nb_referees'] = ''
    df['instructions'] = ''
    df['lit_vec'] = ''

    binary = str('')
    local_path_id = int(-1)
    func_addr = int(-1)

    cnt = 1
    for idx in df.index:
      binary = str(df.at[idx, 'binary'])
      local_path_id = int(df.at[idx, 'local_path_id'])
      func_addr = int(df.at[idx, 'func_addr'])

      path = None
      for p in paths:
        if p[0] == binary and p[1] == local_path_id:
          path = p
          break
      
      if path is None:
        # in case of this error run `/scripts/tpaths_cleanse.py` on the dataset
        print(f"DataError: Path {local_path_id} of {binary} not found at iter {cnt}")
        sys.exit()

      fdata = None
      for f in func_data:
        if f[0] == binary and f[1] == func_addr:
          fdata = f
          break
      
      if fdata is None:
        # in case of this error export function data from the IDB(s) again
        print(f"DataError: Function {hex(func_addr)} of {binary} not found at iter {cnt}")
        sys.exit()

      df.at[idx, 'ref_depth'] = path[2]
      df.at[idx, 'is_upward'] = path[3]
      df.at[idx, 'nb_referrers'] = fdata[2]
      df.at[idx, 'nb_strings'] = fdata[3]
      df.at[idx, 'nb_referees'] = fdata[4]
      df.at[idx, 'instructions'] = fdata[5]
      cnt += 1
    
    # delete non-feature columns
    return df.drop(['binary', 'local_path_id', 'func_addr'], axis=1)

  @staticmethod
  def get_unbalanced_data(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns all labeled token paths (high negative bias), enriched with path and function features."""
    try:
      # big query - faster to join in db than in Python
      # overfetching once is faster than fetching 2*X times or looping X*(Y+Z) times
      # where X - nb of token paths, Y - nb of paths, Z - nb of func data
      # in case of problems with this query (NULL path/func data) run `/scripts/tpaths_cleanse.py` on the dataset
      # or export function data from the IDB(s) again
      cur.execute('''
                  SELECT token_literal, names_func, ref_depth, is_upward, nb_referrers, nb_strings, nb_referees, instructions
                  FROM (SELECT * FROM token_paths WHERE names_func IS NOT NULL) AS tp
                  JOIN (SELECT * FROM paths WHERE to_name IS NOT NULL) AS p ON tp.binary = p.binary AND tp.local_path_id = p.local_id
                  JOIN funcs ON p.binary = funcs.binary AND p.func_addr = funcs.func_addr
                  ''')
      tpaths = cur.fetchall()
    # 'no such table: x'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

    print("Structuring data...")
    df = pd.DataFrame(data=tpaths, columns=_COLUMNS)
    df['lit_vec'] = ''
    return df

  @staticmethod
  def get_embedder_path() -> str:
    """Returns the path to FastText model file (only supports Windows paths)."""
    models_path, _ = os.path.split(os.getcwd())
    return os.path.join(models_path, 'embedder\\embedder.ft')

  @staticmethod
  def get_model_path(filename: str) -> str:
    """Returns the target path for model file."""
    models_path, _ = os.path.split(os.getcwd())
    return os.path.join(models_path, filename)

  @staticmethod
  def load_ft(path: str) -> FastText:
    """Loads a pretrained FastText model from a file."""
    return FastText.load(path)

  @staticmethod
  def split_dataset(features: pd.DataFrame, labels: pd.DataFrame) -> tuple:
    """Parameterized wrapper for `sklearn.model_selection.train_test_split` for classifier training."""
    # Deterministic shuffle
    x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=_TEST_SIZE_RATIO, random_state=0)
    return x_train, x_test, y_train, y_test
  
  @staticmethod
  def ft_embed(ft: FastText, df: pd.DataFrame):
    """Performs vectorization on token text data."""
    df['lit_vec'] = ''
    for idx in df.index:
      df.at[idx, 'lit_vec'] = ft.wv[df.at[idx, 'token_literal']]
    return df

  @staticmethod
  def listify(df: pd.DataFrame) -> list:
    """Transforms the vectorized token literal from `numpy.array` into a single-element list, then converts `pd.DataFrame` to list."""
    for idx in df.index:
      df.at[idx, 'lit_vec'] = df.at[idx, 'lit_vec'].tolist()
    
    return df.values.tolist()
  
  @staticmethod
  def save_results(results: dict, table: str, dbpath: str):
    """Saves test results to results database (or overwrites existing)."""
    conn = sqlite3.connect(dbpath)
    cur = conn.cursor()

    try:
      # sql injection yay (table names cant be passed as params)
      cur.execute(f'DROP TABLE IF EXISTS {table}')
      cur.execute(f'''CREATE TABLE {table} (
                  pos INTEGER NOT NULL,
                  neg INTEGER NOT NULL,
                  tp INTEGER NOT NULL,
                  tn INTEGER NOT NULL,
                  fp INTEGER NOT NULL,
                  fn INTEGER NOT NULL,
                  accuracy REAL NOT NULL,
                  precision REAL NOT NULL,
                  recall REAL NOT NULL,
                  f1 REAL NOT NULL)''')
    except Exception as ex:
      print(ex)
      sys.exit()

    conn.commit()
    pos = int(results['pos'])
    neg = int(results['neg'])
    tp = int(results['tp'])
    tn = int(results['tn'])
    fp = int(results['fp'])
    fn = int(results['fn'])
    acc = float(results['accuracy'])
    precision = float(results['precision'])
    recall = float(results['recall'])
    f1 = float(results['f1'])
    try:
      # sql injection yay (table names cant be passed as params)
      cur.execute(f'INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (pos, neg, tp, tn, fp, fn, acc, precision, recall, f1))
    except Exception as ex:
      print(ex)
      sys.exit()

    conn.commit()
    conn.close()
