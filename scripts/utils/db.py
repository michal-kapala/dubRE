class DbException(Exception):
  """SQLite database exception."""
  def __init__(self, message):            
    super().__init__(message)
