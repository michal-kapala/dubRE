import sqlite3, sys, os, pandas as pd
from gensim.models import FastText
from sklearn.model_selection import train_test_split

_COLUMNS = ['literal', 'is_name']
_TEST_SIZE_RATIO = 0.2
"""Desired percentage of test samples in the dataset."""

class NameClassifierUtils:
  """Utility functions for function name classifiers."""
  @staticmethod
  def query_tokens(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns all labelled tokens from the dataset."""
    try:
      cur.execute('SELECT literal, is_name FROM tokens WHERE is_name IS NOT NULL')
      tokens = cur.fetchall()
    # 'no such table: x'
    except sqlite3.OperationalError as ex:
      print(ex)
      sys.exit()

    return pd.DataFrame(data=tokens, columns=_COLUMNS)

  @staticmethod
  def query_pdb(cur: sqlite3.Cursor) -> pd.DataFrame:
    """Returns all PDB function names from the dataset."""
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
  def split_dataset(features: pd.DataFrame, labels: pd.DataFrame) -> tuple:
    """Parameterized wrapper for `sklearn.model_selection.train_test_split` for classifier training."""
    # Deterministic shuffle
    x_train, x_test, y_train, y_test = train_test_split(features, labels, test_size=_TEST_SIZE_RATIO, random_state=0)
    return x_train, x_test, y_train, y_test
  
  @staticmethod
  def ft_embed(ft: FastText, tokens: pd.DataFrame):
    """Performs vectorization on token text data."""
    tokens['lit_vec'] = ''
    for idx in tokens.index:
      tokens.at[idx, 'lit_vec'] = ft.wv[tokens.at[idx, 'literal']]
    return tokens

  @staticmethod
  def listify(lst: list) -> list[list]:
    """Transforms `list[numpy.array]` into a `list[list[any]]`."""
    result = []
    for elem in lst:
      result.append([elem.tolist()])
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
