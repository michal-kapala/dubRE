import idaapi, idc, sark
import sqlite3
import os, platform


def get_filename():
  """Returns the extensionless IDB file name."""
  path = idc.get_input_file_path()
  return os.path.splitext(os.path.basename(path))[0]

def export_funcs():
  """Exports a function's from-references from IDB to SQLite database (`xrefs` table) in the current directory."""
  filename = get_filename() + '.db'
  trailing_slash = "\\" if platform.system() == "Windows" else "/"
  print("Exporting xrefs to " + os.getcwd() + trailing_slash + filename)
  
  conn = sqlite3.connect(filename)
  conn.text_factory = lambda x: x.decode("utf-8")
  c = conn.cursor()

  # Create function features table
  c.execute('''CREATE TABLE IF NOT EXISTS funcs (
              id INTEGER PRIMARY KEY,
              func_addr INTEGER NOT NULL,
              nb_referrers INTEGER,
              nb_strings INTEGER,
              nb_referees INTEGER,
              instructions INTEGER)''')
  
  funcs = sark.functions()
  exported = 0 
  for func in funcs:
    c.execute('''INSERT INTO funcs (func_addr) VALUES (?)''', (func.ea,))
    exported += 1

  print("Exported " + str(exported) + " functions.")
  conn.commit()
  conn.close()


class FuncExporterPlugin(idaapi.plugin_t):
  flags = idaapi.PLUGIN_PROC
  comment = "dubRE Function Exporter"
  help = "This plugin exports function addresses to SQLite database."
  wanted_name = "dubRE Function Exporter"
  wanted_hotkey = "Shift+F"

  def init(self):
    return idaapi.PLUGIN_KEEP

  def term(self):
    pass

  def run(self, arg):
    export_funcs()


def PLUGIN_ENTRY():
  return FuncExporterPlugin()
