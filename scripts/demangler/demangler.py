from typing import Tuple


SPECIAL_NAME_CODES = {
  "0": "constructor",
  "1": "destructor",
  "2": "operator new",
  "3": "operator delete",
  "4": "operator =",
  "5": "operator >>",
  "6": "operator <<",
  "7": "operator !",
  "8": "operator ==",
  "9": "operator !=",
  "A": "operator[]",
  "B": "",
  "C": "operator ->",
  "D": "operator *",
  "E": "operator ++",
  "F": "operator --",
  "G": "operator -",
  "H": "operator +",
  "I": "operator &",
  "J": "operator ->*",
  "K": "operator /",
  "L": "operator %",
  "M": "operator <",
  "N": "operator <=",
  "O": "operator >",
  "P": "operator >=",
  "Q": "operator,",
  "R": "operator ()",
  "S": "operator ~",
  "T": "operator ^",
  "U": "operator |",
  "V": "operator &&",
  "W": "operator ||",
  "X": "operator *=",
  "Y": "operator +=",
  "Z": "operator -=",
  "_0": "operator /=",
  "_1": "operator %=",
  "_2": "operator >>=",
  "_3": "operator <<=",
  "_4": "operator &=",
  "_5": "operator |=",
  "_6": "operator ^=",
  "_7": "",
  "_8": "",
  "_9": "",
  "_A": "",
  "_B": "",
  "_C": "",
  "_D": "",
  "_E": "",
  "_F": "",
  "_G": "",
  "_H": "",
  "_I": "",
  "_J": "",
  "_K": "",
  "_L": "",
  "_M": "",
  "_N": "",
  "_O": "",
  "_P": "",
  "_Q": "",
  "_R": "",
  "_S": "",
  "_T": "",
  "_U": "operator new[]",
  "_V": "operator delete[]",
  "_W": "",
  "_X": "",
  "_Y": "",
  "_Z": "",
  # __X codes are ignored
}
"""Special name code mapping (empty are ignored)."""

class Demangler:
  @staticmethod
  def process_unmangled(name: str) -> str:
    """Returns the core name of a function from unmangled signature."""
    result = ""
    for char in name:
      if char in ["@", "$"]:
        return result
      result += char
    return result
  
  @staticmethod
  def process_mangled(name: str) -> str:
    """Returns the core name of a function from mangled signature."""
    result = ""
    match name[1]:
      case "?":
        if name[2] == "$":
          # ignore "??$?<...>"
          if name[3] == "?":
            return result
          else:
            result = Demangler.__read_template(name)  
        else:
          result = Demangler.__read_special(name)
      case _:
        result = Demangler.__read_mangled(name)
    
    return result
  
  @staticmethod
  def __read(name: str, offset: int) -> Tuple[(str, str)]:
    """Reads name and basic qualification of a mangled symbol."""
    core = ""
    qualification = ""
    namespaces = []
    
    current = ""
    for idx in range(offset, len(name)):
      # identifier
      if name[idx].isidentifier() or name[idx].isnumeric():
        current += name[idx]
      # single @ - simple qualification separator
      elif name[idx] == "@" and (name[idx - 1].isidentifier() or name[idx - 1].isnumeric()):
        if core == "":
          
          core = current
        else:
          # reverses order
          namespaces.insert(0, current)

        current = ""
      # special character - end
      else:
        break
    
    for ns in namespaces:
      qualification += ns + "::"

    return (qualification, core)

  @staticmethod
  def __read_mangled(name: str) -> str:
    """Reads a simply mangled or nested name function symbol."""
    (qualif, core) = Demangler.__read(name, 1)
    return qualif + core
  
  @staticmethod
  def __read_special(name: str) -> str:
    """Reads a special name function symbol."""
    # read code
    code = name[2]
    if code == "_":
      code += name[3]

    # the name should be ignored
    if code == "__" or SPECIAL_NAME_CODES[code] == "":
      return ""
    
    # ignore "??X@<...>" and "??XX@<...>"
    if name[2 + len(code)] == "@":
      return ""
    
    match code:
      case "0":
        offset = 5 if name[3] == "?" and name[4] == "$" else 3
        (qualif, core) = Demangler.__read(name, offset)

        return f"{qualif}{core}::{core}"

      case "1":
        offset = 5 if name[3] == "?" and name[4] == "$" else 3
        (qualif, core) = Demangler.__read(name, offset)

        return f"{qualif}{core}::~{core}"
      
      case (
      "2" |
      "3" |
      "4" |
      "5" |
      "6" |
      "7" |
      "8" |
      "9" |
      "A" |
      "C" |
      "D" |
      "E" |
      "F" |
      "G" |
      "H" |
      "I" |
      "J" |
      "K" |
      "L" |
      "M" |
      "N" |
      "O" |
      "P" |
      "Q" |
      "R" |
      "S" |
      "T" |
      "U" |
      "V" |
      "W" |
      "X" |
      "Y" |
      "Z"):
        offset = 5 if name[3] == "?" and name[4] == "$" else 3
        (qualif, core) = Demangler.__read(name, offset)

        return f"{qualif}{core}::{SPECIAL_NAME_CODES[code]}"
      case (
      "_0" |
      "_1" |
      "_2" |
      "_3" |
      "_4" |
      "_5" |
      "_6" |
      "_U" |
      "_V"):
        offset = 6 if name[4] == "?" and name[5] == "$" else 4
        (qualif, core) = Demangler.__read(name, offset)
        return f"{qualif}{core}::{SPECIAL_NAME_CODES[code]}"
      case _:
        raise Exception(f"Unknown special name code: {code}")
    
  @staticmethod
  def __read_template(name: str) -> str:
    """Reads a templated args function symbol."""
    (qualif, core) = Demangler.__read(name, 3)
    return qualif + core
