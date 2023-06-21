import idaapi, idc, sark
import sqlite3
import os, platform

MAX_UP_REFERENCE_DEPTH = 1
"""Maximal evaluated distance in upward traversal of reference graph (measured in function calls)."""

MAX_DOWN_REFERENCE_DEPTH = 2
"""Maximal evaluated distance in downward traversal of reference graph (measured in function calls)."""

IDATA = sark.Segment(name=".idata")
"""`.idata` imports section (Sark segment)."""

RDATA = sark.Segment(name=".rdata")
"""`.rdata` data section (Sark segment)."""

def get_filename():
  """Returns the extensionless IDB file name."""
  path = idc.get_input_file_path()
  return os.path.splitext(os.path.basename(path))[0]

def is_import(ea):
  """Checks if an address belongs to `.idata` section."""
  return ea >= IDATA.ea and ea < IDATA.ea + IDATA.size

def is_before_rdata(ea):
  """Checks if the address is from before `.rdata` section."""
  return ea < RDATA.ea

def is_tostring_xref(xref):
  """Checks if cross reference points to a string."""
  # IDAPython docs say it returns empty string on failure but it actually returns None
  # https://www.hex-rays.com/products/ida/support/idapython_docs/idc.html#idc.get_strlit_contents
  return xref.type.is_data and idc.get_strlit_contents(xref.to) not in [None, ""] and not is_before_rdata(xref.to)

def traverse_referrer_referee(cur, top_func, path_func1, path_func2, path_func3, ref_depth, is_upward):
  """Adds string xrefs from a referrer or referee function."""
  # depth checks
  ref_depth += 1
  if not is_upward and ref_depth > MAX_DOWN_REFERENCE_DEPTH:
    return
  
  if is_upward and ref_depth > MAX_UP_REFERENCE_DEPTH:
    return
  
  # choose passed function
  func = None
  if ref_depth == 1:
    func = sark.Function(path_func1)
  elif ref_depth == 2:
    func = sark.Function(path_func2)
  elif ref_depth == 3:
    func = sark.Function(path_func3)
  else:
    raise Exception("Max reference recursion depth violated: " + str(ref_depth))
    
  # add string references
  for xref in func.xrefs_from:
    # skip all xrefs pointing neither to a function nor a string
    if not is_tostring_xref(xref) and not xref.type.is_code:
      continue

    # skip import xrefs
    if is_import(xref.to):
      continue

    # function xref - traverse downward function xrefs
    if xref.type.is_code and not is_upward:
      if ref_depth == 1:
        traverse_referrer_referee(cur, top_func, path_func1, xref.to, path_func3, ref_depth, False)
      elif ref_depth == 2:
        traverse_referrer_referee(cur, top_func, path_func1, path_func2, xref.to, ref_depth, False)
      elif ref_depth == 3:
        # dont enter 4th depth level
        continue

    # function xref - wrong direction, skip
    elif xref.type.is_code and is_upward:
      continue

    # string xref - add x-level reference
    else:
      try:
        cur.execute("INSERT INTO xrefs (func_addr,string_addr,path_func1,path_func2,path_func3,ref_depth,is_upward) VALUES (?,?,?,?,?,?,?)", (
          top_func, xref.to, path_func1, path_func2, path_func3, ref_depth, is_upward
          ))
      except sqlite3.IntegrityError:
        pass
    
  # traverse upward function xrefs
  if is_upward and ref_depth < MAX_UP_REFERENCE_DEPTH:
    for xref in func.xrefs_to:
      # functions can only be referenced by other functions
      if not xref.type.is_code:
        continue
      # skip xrefs from instruction blocks (unstructured functions)
      if idc.get_func_name(xref.frm) == "":
        continue
      
      if ref_depth == 1:
        traverse_referrer_referee(cur, top_func, path_func1, xref.frm, path_func3, ref_depth, True)
      elif ref_depth == 2:
        traverse_referrer_referee(cur, top_func, path_func1, path_func2, xref.frm, ref_depth, True)
      else:
        raise Exception("Unimplemented reference recursion depth for MAX_REF_DEPTH=" + str(MAX_DOWN_REFERENCE_DEPTH))


def export_xrefs():
  """Exports a function's from-references from IDB to SQLite database (`xrefs` table) in the current directory."""
  filename = get_filename() + '.db'
  trailing_slash = "\\" if platform.system() == "Windows" else "/"
  print("Exporting xrefs to " + os.getcwd() + trailing_slash + filename)
  
  conn = sqlite3.connect(filename)
  conn.text_factory = lambda x: x.decode("utf-8")
  c = conn.cursor()

  # Create function-string xrefs table
  c.execute('''CREATE TABLE IF NOT EXISTS xrefs (
              id INTEGER PRIMARY KEY,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              path_func1 INTEGER,
              path_func2 INTEGER,
              path_func3 INTEGER,
              ref_depth INTEGER NOT NULL,
              is_upward INTEGER NOT NULL,
              UNIQUE (func_addr, string_addr, path_func1, path_func2, path_func3))''')
  
  # Create function-token xrefs table
  c.execute('''CREATE TABLE IF NOT EXISTS xref_tokens (
              xref_id INTEGER NOT NULL,
              func_addr INTEGER NOT NULL,
              string_addr INTEGER NOT NULL,
              token_literal TEXT NOT NULL,
              names_func INTEGER)''')
  
  # Export xrefs to db
  exported = 0
  
  ref_depth = 0

  for func in sark.functions():
    # level 0 - downward search
    for xref in func.xrefs_from:
      # skip all xrefs pointing neither to a function nor a string
      if not is_tostring_xref(xref) and not xref.type.is_code:
        continue

      # skip import xrefs
      if is_import(xref.to):
        continue

      # function xref - traverse reference graph neighbours
      if xref.type.is_code:
        # using -1 because SQLite treats NULL as a unique value
        # and as a consequence doesn't honor the multi-column UNIQUE constraint
        # https://stackoverflow.com/a/2701903/14807735
        traverse_referrer_referee(c, func.ea, xref.to, -1, -1, ref_depth, False)
      # string xref - add 0-level reference
      else:
        try:
          c.execute("INSERT INTO xrefs (func_addr,string_addr,path_func1,path_func2,path_func3,ref_depth,is_upward) VALUES (?,?,?,?,?,?,?)", (
            func.ea, xref.to, -1, -1, -1, 0, False
            ))
          exported += 1
        except sqlite3.IntegrityError:
          pass

    # level 0 - upward search
    for xref in func.xrefs_to:
      # functions can only be referenced by other functions
      if not xref.type.is_code:
        continue
      # skip xrefs from instruction blocks (unstructured functions)
      if idc.get_func_name(xref.frm) == "":
        continue

      # function xref - traverse reference graph neighbours
      if xref.type.is_code:
        traverse_referrer_referee(c, func.ea, xref.frm, -1, -1, ref_depth, True)

  print("Exported " + str(exported) + " zero-level xref paths.")
  conn.commit()
  conn.close()


class XrefExporterPlugin(idaapi.plugin_t):
  flags = idaapi.PLUGIN_PROC
  comment = "dubRE Xref Path Exporter"
  help = "This plugin exports cross-reference paths to SQLite database."
  wanted_name = "dubRE XRef Path Exporter"
  wanted_hotkey = "Shift+X"

  def init(self):
    return idaapi.PLUGIN_KEEP

  def term(self):
    pass

  def run(self, arg):
    export_xrefs()


def PLUGIN_ENTRY():
  return XrefExporterPlugin()
