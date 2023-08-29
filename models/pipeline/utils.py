import sqlite3, sys, os, pandas as pd
from gensim.models import FastText
from sklearn.model_selection import train_test_split

_TPATH_COLUMNS = [
  'binary',
  'func_addr',
  'ref_depth',
  'is_upward',
  'token_literal',
  'names_func',
  'nb_referrers',
  'nb_strings',
  'nb_referees',
  'instructions']
_TOKEN_COLUMNS = ['literal', 'is_name']
_TEST_SIZE_RATIO = 0.2
"""Desired percentage of test samples in the dataset. Needs to stay the same across all evaluated models."""

class PipelineUtils:
  """Utility functions for pipeline simulation."""
  @staticmethod
  def query_data(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns paths/token paths/funcs join for the pipeline."""
    try:
      cur.execute('''SELECT p.binary, p.func_addr, ref_depth, is_upward, token_literal, names_func, nb_referrers, nb_strings, nb_referees, instructions FROM (SELECT binary, local_id, func_addr, ref_depth, is_upward FROM paths WHERE to_name IS NOT NULL) AS p
                    JOIN token_paths AS tp ON p.binary = tp.binary AND local_id = local_path_id
                    JOIN funcs ON funcs.binary = p.binary AND funcs.func_addr = p.func_addr
                    WHERE names_func IS NOT NULL''')
      data = cur.fetchall()
    # 'no such table: x'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

    # test dataset of paths models
    # use `seen_tokens.py` to calculate percentage of token data used in name classifiers' training
    _, test_data = train_test_split(data, test_size=_TEST_SIZE_RATIO, random_state=0)

    return pd.DataFrame(test_data, columns=_TPATH_COLUMNS)

  @staticmethod
  def query_tokens(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns all labelled tokens from the dataset (from `models/names/utils.py`)."""
    try:
      cur.execute('SELECT literal, is_name FROM tokens WHERE is_name IS NOT NULL')
      tokens = cur.fetchall()
    # 'no such table: x'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

    return pd.DataFrame(data=tokens, columns=_TOKEN_COLUMNS)

  @staticmethod
  def query_pdb(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns all PDB function names from the dataset (from `models/names/utils.py`)."""
    try:
      cur.execute('SELECT literal FROM pdb')
      pdb = cur.fetchall()
    # 'no such table: x'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()
    df = pd.DataFrame(data=pdb, columns=['literal'], index=range(len(pdb)))
    
    df['is_name'] = ''
    for idx in df.index:
      df.at[idx, 'is_name'] = 1

    return df

  @staticmethod
  def balance_dataset(tokens_df: pd.DataFrame, pdb_df: pd.DataFrame) -> pd.DataFrame:
    """Returns a complete dataset balanced with PDB positives."""
    # calculate the nb of missing positives
    nb_neg = tokens_df[tokens_df['is_name'] == 0].shape[0]
    nb_pos = tokens_df.shape[0] - nb_neg
    nb_missing_pos = nb_neg - nb_pos

    # deterministic shuffle
    balancing_pos, _ = train_test_split(pdb_df, train_size=nb_missing_pos, random_state=0)
    return pd.concat([tokens_df, balancing_pos], ignore_index=True)

  @staticmethod
  def split_dataset(df: pd.DataFrame) -> tuple:
    """Wrapper for `sklearn.model_selection.train_test_split`."""
    # Deterministic shuffle
    x_train, x_test = train_test_split(df, test_size=_TEST_SIZE_RATIO, random_state=0)
    return x_train, x_test

  @staticmethod
  def get_model_path(filename: str) -> str:
    """Returns the target path for model file."""
    models_path, _ = os.path.split(os.getcwd())
    return os.path.join(models_path, filename)
  
  @staticmethod
  def get_embedder_path() -> str:
    """Returns the path to FastText model file (only supports Windows paths)."""
    models_path, _ = os.path.split(os.getcwd())
    return os.path.join(models_path, 'embedder\\embedder.ft')

  @staticmethod
  def load_ft(path: str) -> FastText:
    """Loads a pretrained FastText model from a file."""
    return FastText.load(path)
  
  @staticmethod
  def ft_embed(ft: FastText, df: pd.DataFrame):
    """Performs vectorization on token text data."""
    df['lit_vec'] = ''
    for idx in df.index:
      df.at[idx, 'lit_vec'] = ft.wv[df.at[idx, 'token_literal']]
    return df
  
  @staticmethod
  def listify_paths(df: pd.DataFrame) -> list:
    """Transforms the vectorized token literal from `numpy.array` into a single-element list, then converts `pd.DataFrame` to list."""
    for idx in df.index:
      df.at[idx, 'lit_vec'] = df.at[idx, 'lit_vec'].tolist()
    
    return df.values.tolist()
  
  @staticmethod
  def listify_names(lst: list) -> list[list]:
    """Transforms `list[numpy.array]` into a `list[list[any]]`."""
    result = []
    for elem in lst:
      result.append([elem.tolist()])
    return result

  @staticmethod
  def group_in_funcs(df: pd.DataFrame) -> dict:
    """Returns a dict with functions->token paths hierarchy."""
    mapping = {}
    for idx in df.index:
      binary = df.at[idx, 'binary']
      # func = df.at[idx, 'func_addr']
      mapping[binary] = {}

    for idx in df.index:
      binary = df.at[idx, 'binary']
      func = df.at[idx, 'func_addr']
      mapping[binary][func] = []

    for idx in df.index:
      binary = df.at[idx, 'binary']
      func = df.at[idx, 'func_addr']
      mapping[binary][func].append(df.iloc[idx].to_list())

    result = []
    for bkey in mapping:
      for fkey in mapping[bkey]:
        result.append(mapping[bkey][fkey])

    return result

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
                  precision REAL,
                  recall REAL,
                  f1 REAL)''')
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
    precision = float(results['precision']) if results['precision'] is not None else None
    recall = float(results['recall']) if results['recall'] is not None else None
    f1 = float(results['f1']) if results['f1'] is not None else None
    try:
      # sql injection yay (table names cant be passed as params)
      cur.execute(f'INSERT INTO {table} VALUES (?,?,?,?,?,?,?,?,?,?)',
                  (pos, neg, tp, tn, fp, fn, acc, precision, recall, f1))
    except Exception as ex:
      print(ex)
      sys.exit()

    conn.commit()
    conn.close()