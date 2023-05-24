import idaapi, idc
import sqlite3
import os, platform

def get_filename():
    """Returns the extensionless IDB file name."""
    path = idc.get_input_file_path()
    return os.path.splitext(os.path.basename(path))[0]

def make_string(sc):
    """Makes an IDA-searchable string out of `string_info_t` item."""
    return idaapi.get_ascii_contents(
        sc.ea, sc.length, sc.type
        ).replace(
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

def export_strings():
    """Exports unique strings from IDB to SQLite database (`strings` table) in the current directory."""
    filename = get_filename() + '.db'
    trailing_slash = "\\" if platform.system() == "Windows" else "/"
    print("Exporting strings to " + os.getcwd() + trailing_slash + filename)
    
    conn = sqlite3.connect(filename)
    conn.text_factory = lambda x: x.decode("utf-8")
    c = conn.cursor()

    # Create table
    c.execute('''CREATE TABLE IF NOT EXISTS strings
                (address integer UNIQUE, literal text UNIQUE)''')
    
    # Export strings to db
    sc = idaapi.string_info_t()
    exported = 0
    
    for i in range(0, idaapi.get_strlist_qty()):
        idaapi.get_strlist_item(sc, i)
        try:
            c.execute("INSERT INTO strings VALUES (?,?)", (sc.ea, make_string(sc)) )
            exported += 1
        # Skip duplicate errors on UNIQUE db constraint ('column X is not unique')
        except sqlite3.IntegrityError:
            pass

    print("Exported " + str(exported) + " unique strings.")
    conn.commit()
    conn.close()


class StringExporterPlugin(idaapi.plugin_t):
    flags = idaapi.PLUGIN_PROC
    comment = "dubRE String Exporter"
    help = "This plugin exports unique strings to SQLite database; encoding as-seen in Strings subview."
    wanted_name = "dubRE String Exporter"
    wanted_hotkey = "Shift+S"

    def init(self):
        return idaapi.PLUGIN_KEEP

    def term(self):
        pass

    def run(self, arg):
        export_strings()


def PLUGIN_ENTRY():
    return StringExporterPlugin()
