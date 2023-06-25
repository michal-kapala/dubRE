import idaapi, idc, sark
import sqlite3
import os, platform


IDATA = sark.Segment(name=".idata")
"""`.idata` imports section (Sark segment)."""

RDATA = sark.Segment(name=".rdata")
"""`.rdata` data section (Sark segment)."""

def get_filename():
  """Returns the extensionless IDB file name (removes `-stripped` suffix)."""
  path = idc.get_input_file_path()
  return os.path.splitext(os.path.basename(path))[0].replace("-stripped", "")

def is_import(ea):
  """Checks if an address belongs to `.idata` section."""
  return ea >= IDATA.ea and ea < IDATA.ea + IDATA.size

def is_before_rdata(ea):
  """Checks if the address is from before `.rdata` section."""
  return ea < RDATA.ea

def is_tostring_xref(xref):
  """Checks if cross reference points to a string."""
  # IDAPython docs say `get_strlit_contents` returns empty strings on failure but it actually returns None
  # https://www.hex-rays.com/products/ida/support/idapython_docs/idc.html#idc.get_strlit_contents
  return (
    xref.type.is_data
    and idc.get_strlit_contents(xref.to) not in [None, ""]
    and not is_before_rdata(xref.to)
    and not is_import(xref.to)
  )

def get_nb_xref_to(ea):
  """Returns the number of code references to a function."""
  func = sark.Function(ea)
  unique = []

  for xref in func.xrefs_to:
    if xref.type.is_code and xref.frm not in unique:
      unique.append(xref.frm)

  return len(unique)


def get_nb_xref_from(ea):
  """Returns the number of code references from a function."""
  func = sark.Function(ea)
  unique = []
  
  for xref in func.xrefs_from:
    if xref.type.is_code and xref.to not in unique:
      unique.append(xref.to)

  return len(unique)

def get_nb_strings(ea):
  """Returns the number of function's string xrefs."""
  func = sark.Function(ea)
  unique = []
  
  for xref in func.xrefs_from:
    if is_tostring_xref(xref) and xref.to not in unique:
        unique.append(xref.to)

  return len(unique)

def export_func_data():
  """Exports a function data to SQLite db (`funcs` table) in the current directory."""
  filename = get_filename() + '.db'
  trailing_slash = "\\" if platform.system() == "Windows" else "/"
  print("Exporting function data to " + os.getcwd() + trailing_slash + filename)
  
  conn = sqlite3.connect(filename)
  conn.text_factory = lambda x: x.decode("utf-8")
  c = conn.cursor()

  # Fetch addresses
  c.execute("SELECT func_addr FROM funcs")
  addrs = c.fetchall()
  func_cnt = 0

  for row in addrs:
    addr = row[0]
    func = sark.Function(addr)
    func_cnt += 1
    print(str(func_cnt) + " - " + func.name)

    nb_referrers = get_nb_xref_to(addr)
    nb_strings = get_nb_strings(addr)
    nb_referees = get_nb_xref_from(addr)
    nb_lines = len(list(func.lines))

    c.execute('''UPDATE funcs SET
      nb_referrers = ?,
      nb_strings = ?,
      nb_referees = ?,
      instructions = ?
      WHERE func_addr = ?''',
      (nb_referrers, nb_strings, nb_referees, nb_lines, addr))

  print("Exported all functions.")
  conn.commit()
  conn.close()


class FuncDataExporterPlugin(idaapi.plugin_t):
  flags = idaapi.PLUGIN_PROC
  comment = "dubRE Function Data Exporter"
  help = "This plugin exports basic function data to SQLite database."
  wanted_name = "dubRE Function Data Exporter"
  wanted_hotkey = "Shift+D"

  def init(self):
    return idaapi.PLUGIN_KEEP

  def term(self):
    pass

  def run(self, arg):
    export_func_data()


def PLUGIN_ENTRY():
  return FuncDataExporterPlugin()
