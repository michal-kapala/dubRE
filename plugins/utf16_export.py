import idaapi, idc
import sqlite3
import os, platform

def get_filename():
    """Returns the extensionless IDB file name."""
    path = idc.get_input_file_path()
    return os.path.splitext(os.path.basename(path))[0]

def fix_whitespace(literal):
    """Replaces whitespace characters with corresponding literals."""
    if literal is None:
        return literal

    literal = literal.replace(
    "\\", "\\\\"
    ).replace(
    "\t", "\\t"
    ).replace(
    "\r", "\\r"
    ).replace(
    "\n", "\\n"
    ).replace(
    "\b", "\\b"
    ).replace(
    "\v", "\\v"
    ).replace(
    "\a", "\\a"
    ).replace(
    "\f", "\\f"
    ).replace(
    "\x1b", "\\x1B"
    )

    return literal

def export_strings():
    """Exports missing strings (referenced from `paths`) from IDB to SQLite database (`strings`) in the current directory."""
    filename = get_filename() + '.db'
    trailing_slash = "\\" if platform.system() == "Windows" else "/"
    print("Exporting missing strings to " + os.getcwd() + trailing_slash + filename)
    
    conn = sqlite3.connect(filename)
    conn.text_factory = lambda x: x.decode("utf-8")
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS strings
                (address integer UNIQUE, literal text UNIQUE)''')
    
    try:
        c.execute('''SELECT * FROM (SELECT string_addr, count(*) from paths GROUP BY string_addr) AS pstrings LEFT JOIN strings ON pstrings.string_addr = strings.address WHERE literal IS NULL''')
        missing = c.fetchall()
    except:
        raise Exception("Could not query the missing strings. Make sure you have a populated `paths` table.")

    exported = 0
    duplicates = 0
    for row in missing:
        string_addr = row[0]

        # Try exporting as UTF-16 string
        literal = fix_whitespace(idc.get_strlit_contents(string_addr, -1, 1))

        if literal is None or literal == "":
            # Try exporting as a UTF-8 string
            literal = fix_whitespace(idc.get_strlit_contents(string_addr, -1, 0))
            if literal is None or literal == "":
                print("Error: could not export string at " + str(hex(string_addr)))
                continue

        try:
            c.execute("INSERT INTO strings VALUES (?,?)", (string_addr, literal))
            exported += 1
        # Skip duplicate errors on UNIQUE db constraint ('column X is not unique')
        except sqlite3.IntegrityError:
            duplicates += 1
            pass

    print("Exported " + str(exported) + " unique strings.")
    print("Skipped " + str(duplicates) + " duplicates.")
    conn.commit()
    conn.close()


class Utf16StringExporterPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC
    comment = "dubRE UTF-16 String Exporter"
    help = "This plugin exports missing UTF-16 and UTF-8 strings to SQLite database; `paths` table is required."
    wanted_name = "dubRE UTF-16 String Exporter"
    wanted_hotkey = "Shift+M"

    def init(self):
        return idaapi.PLUGIN_KEEP

    def term(self):
        pass

    def run(self, arg):
        export_strings()


def PLUGIN_ENTRY():
    return Utf16StringExporterPlugin()
