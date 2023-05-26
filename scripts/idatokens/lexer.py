from enum import Enum
from typing import List

LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def isletter(char: str) -> bool:
  """Checks if the character is an ASCII letter."""
  return char in LETTERS

class MetaTokenType(Enum):
  """Meta token types used for pre-tokenization."""
  REGULAR = 0
  """Alphanumeric or underscore"""
  SCOPE_RES = 1
  """`::`"""
  LEFT_ANGLE = 2
  """`<`"""
  RIGHT_ANGLE = 3
  """`>`"""
  SPACE = 4
  """Space character"""
  TILDA = 5
  """`~`"""
  OPERATOR = 6
  """`operator` keyword"""
  DOT = 7
  """`.`"""
  LEFT_PARENTH = 8
  """`(`"""
  RIGHT_PARENTH = 9
  """`)`"""
  COMMA = 10
  """`,`"""
  EQUALS = 11
  """`=`"""
  PLUS = 12
  """`+`"""
  HYPHEN = 13
  """`-`"""
  STAR = 14
  """`*`"""
  SLASH = 15
  """`/`"""
  BACKSLASH = 16
  """`\`"""
  COLON = 17
  """`:`"""
  SEMICOLON = 18
  """`;`"""
  EXCLAMATION = 19
  """`!`"""
  QUESTION = 20
  """`?`"""
  LEFT_SQUARE = 21
  """`[`"""
  RIGHT_SQUARE = 22
  """`]`"""
  AND = 23
  """`&`"""
  PIPE = 24
  """`|`"""
  PERCENT = 25
  """`%`"""
  CARET = 26
  """`^`"""
  QUOTE = 27
  """`'`"""
  DQUOTE = 28
  """`"`"""
  BACKTICK = 29
  """`"""
  NEW = 30
  """`new` keyword"""
  DELETE = 31
  """`delete` keyword"""
  AT = 32
  """`@`"""
  HASH = 33
  """`#`"""
  DOLLAR = 34
  """`$`"""
  LEFT_CURLY = 35
  """`{`"""
  RIGHT_CURLY = 36
  """`}`"""
  OTHER = 37
  """Some weird non-ASCII character"""

class MetaToken:
  def __init__(self, token: str, type: MetaTokenType) -> None:
    self.token = token
    self.type = type
  
  def __str__(self):
    return "{'" + self.token + "', " + self.type.name + "}"

class StringLexer:
  def __init__(self, string: str) -> None:
    self.str = string
    self.pos = 0

  def current(self) -> str:
    """Returns currently processed character."""
    return self.str[self.pos]
    
  def next(self) -> str| None:
    """Returns next character or `None` if end of string was reached."""
    if self.next_pos() == None:
      return None
    return self.str[self.pos + 1]
  
  def next_pos(self) -> int | None:
    """Returns next position or `None` if end of string was reached."""
    if self.pos + 1 == len(self.str):
      return None
    return self.pos + 1
  
  def consume(self) -> str:
    """Returns and consumes the current character."""
    self.pos += 1
    return self.str[self.pos - 1]
  
  def reset(self, new_str: str) -> None:
    """Initializes lexer with a new string."""
    self.str = new_str
    self.pos = 0

  def empty(self) -> bool:
    """Checks if there are characters left for processing."""
    return self.pos == len(self.str)

  def metatokens(self) -> List[MetaToken]:
    metatokens = []

    while not self.empty():
      token_str = ""
      cur = self.current()
      # append if alphanumeric (accepts chinese etc.)
      while not self.empty() and (isletter(cur) or cur.isdigit() or cur == "_"):
        token_str += self.consume()
        cur = self.current()
        print(f"token_str: {token_str}")
      # add a token
      if len(token_str) > 0:
        # mark operator keywords
        if token_str == "operator":
          metatokens.append(MetaToken(token_str, MetaTokenType.OPERATOR))
        elif token_str == "new":
          metatokens.append(MetaToken(token_str, MetaTokenType.NEW))
        elif token_str == "delete":
          metatokens.append(MetaToken(token_str, MetaTokenType.DELETE))
        else:
          metatokens.append(MetaToken(token_str, MetaTokenType.REGULAR))
      else:
        # handle special characters
        match cur:
          # the angles
          case "<":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.LEFT_ANGLE))
          case ">":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.RIGHT_ANGLE))
          # the colon
          case ":":
            token_str += self.consume()
            if self.next() == ":":
              token_str += self.consume()
              metatokens.append(MetaToken(token_str, MetaTokenType.SCOPE_RES))
            else:
              metatokens.append(MetaToken(token_str, MetaTokenType.COLON))
          # the tilda
          case "~":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.TILDA))

          # these make up overloadable operators
          case "!":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.EXCLAMATION))
          case "%":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.PERCENT))
          case "^":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.CARET))
          case "&":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.AND))
          case "*":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.STAR))
          case "(":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.LEFT_PARENTH))
          case ")":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.RIGHT_PARENTH))
          case "-":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.HYPHEN))
          case "+":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.PLUS))
          case "=":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.EQUALS))
          case "|":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.PIPE))
          case "[":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.LEFT_SQUARE))
          case "]":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.RIGHT_SQUARE))
          case ",":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.COMMA))
          case "/":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.SLASH))

          # non-overloadable
          case "`":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.BACKTICK))
          case "@":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.AT))
          case "#":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.HASH))
          case "$":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.DOLLAR))
          case "\\":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.BACKSLASH))
          case "{":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.LEFT_CURLY))
          case "}":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.RIGHT_CURLY))
          case ";":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.SEMICOLON))
          case "'":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.QUOTE))
          case "\"":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.DQUOTE))
          case "?":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.QUESTION))
          case ".":
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.DOT))
          case _:
            token_str += self.consume()
            metatokens.append(MetaToken(token_str, MetaTokenType.OTHER))

    return metatokens
