from .lexer import MetaToken, MetaTokenType, Lexer
from .preparser import PreParser
from typing import List

PATTERNS = [
  # constructors

  # [i, [t], sr]* i, sr, i
  [
    MetaTokenType.IDENTIFIER_LIKE,
    MetaTokenType.SCOPE_RES,
    MetaTokenType.IDENTIFIER_LIKE,
  ],

  # [i, [t], sr]* i, t1, sr, i, t1 [t2]
  [
    MetaTokenType.TEMPLATE_LIKE,
    MetaTokenType.IDENTIFIER_LIKE,
    MetaTokenType.SCOPE_RES,
    MetaTokenType.TEMPLATE_LIKE,
    MetaTokenType.IDENTIFIER_LIKE,
  ],

  # destructors

  # [i, [t], sr]* i, dsr, i
  [
    MetaTokenType.IDENTIFIER_LIKE,
    MetaTokenType.DEST_SCOPE_RES,
    MetaTokenType.IDENTIFIER_LIKE,
  ],

  # [i, [t], sr]* i, t1, dsr, i, t1, [t2]
  [
    MetaTokenType.TEMPLATE_LIKE,
    MetaTokenType.IDENTIFIER_LIKE,
    MetaTokenType.DEST_SCOPE_RES,
    MetaTokenType.TEMPLATE_LIKE,
    MetaTokenType.IDENTIFIER_LIKE,
  ],

  # operators
  
  # [i, [t], sr]* o
  [
    MetaTokenType.OPERATOR_ID,
  ],

  # regular functions

  # [i, [t], sr]* i, t
  [
    MetaTokenType.TEMPLATE_LIKE,
    MetaTokenType.IDENTIFIER_LIKE,
  ],

  # [i, [t], sr]* i
  [
    MetaTokenType.IDENTIFIER_LIKE,
  ],
]
"""Patterns for matching the names of regular functions, overloaded operators, constructors and destructors. Sorted by precedence, token types in reversed order (right-to-left)."""

PATHLIKE_TYPES = [
  MetaTokenType.SLASH,
  MetaTokenType.BACKSLASH,
  MetaTokenType.DBACKSLASH,
  MetaTokenType.IDENTIFIER_LIKE,
  MetaTokenType.REGULAR_LIKE,
  MetaTokenType.NUMBER_LIKE,
  MetaTokenType.DOT,
  MetaTokenType.PATH_LIKE,
]
"""Meta token types accepted in path-like literals."""

NON_JOINABLE = [
  MetaTokenType.OPERATOR_LIKE,
  MetaTokenType.CONSTRUCTOR_LIKE,
  MetaTokenType.DESTRUCTOR_LIKE,
]
"""Tokens unjoinable for `UNDEFINED` neighbours."""

class Tokenizer:
  """Creates labelling-ready tokens out of preprocessed metatokens."""
  def __init__(self, metatokens) -> None:
      self.mtokens = metatokens

  def reset(self, new_mtokens: List[MetaToken] ) -> None:
    """Reinitializes tokenizer with a new mtoken list."""
    self.mtokens = new_mtokens    

  def match_patterns(self):
    """Produces structured tokens with potential function names joined together."""
    result = self.mtokens
    
    # try matching on all patterns
    for pattern_idx in range(0, len(PATTERNS)):
      pattern = PATTERNS[pattern_idx]
      
      # mtokens too short, cannot match
      if len(self.mtokens) < len(pattern):
        continue

      mt_idx = len(self.mtokens) - 1
      # iterate right-to-left and try to match

      while mt_idx >= len(pattern) - 1:
        matched = True
        # if first token does not match, skip to next
        if self.mtokens[mt_idx].type != pattern[0]:
          mt_idx -= 1
          continue

        # match on pattern sequence
        for pt_idx in range(0, len(pattern)):
          if self.mtokens[mt_idx - pt_idx].type != pattern[pt_idx]:
            matched = False
            break
        
        # match failed
        if matched == False:
          mt_idx -= 1
          continue

        # try optional matches
        matched_posttempl = 0
        matched_qual = 0

        # check constructor/destructor post-templating [t]
        if pt_idx in [1, 3] and mt_idx < len(self.mtokens) - 1:
          if self.mtokens[mt_idx + 1].type == MetaTokenType.TEMPLATE_LIKE:
            matched_posttempl = 1

        # check for qualification prefix
        begin = mt_idx - len(pattern)
        # [i, [t], sr]*
        while begin > 0:
          # [i, sr]
          if (self.mtokens[begin].type == MetaTokenType.SCOPE_RES and 
              self.mtokens[begin - 1].type == MetaTokenType.IDENTIFIER_LIKE):
              matched_qual += 2
              begin -= 2
          # [i, t, sr]
          elif (begin > 1 and 
              self.mtokens[begin].type == MetaTokenType.SCOPE_RES and
              self.mtokens[begin - 1].type == MetaTokenType.TEMPLATE_LIKE and
              self.mtokens[begin - 2].type == MetaTokenType.IDENTIFIER_LIKE):
              matched_qual += 3
              begin -= 3
          # end of qualification
          else:
            break

        # join mtokens        
        value = ""
        for pt_idx in range(len(pattern) + matched_qual + matched_posttempl):
          # mt_idx = 9
          # len(pattern) = 5
          value += self.mtokens[mt_idx - (len(pattern) + matched_qual) + 1 + pt_idx].token

        mt_type = None
        match pattern_idx:
          case 0:
            # constructor
            if self.mtokens[mt_idx].token == self.mtokens[mt_idx - 2].token:
              mt_type = MetaTokenType.CONSTRUCTOR_LIKE
            # regular function, match later
            else:
              mt_idx -= 1
              continue
          case 1:
            # constructor
            if (self.mtokens[mt_idx - 1].token == self.mtokens[mt_idx - 4].token and
              self.mtokens[mt_idx].token == self.mtokens[mt_idx - 3].token):
              mt_type = MetaTokenType.CONSTRUCTOR_LIKE
            # regular function, match later
            else:
              mt_idx -= 1
              continue
          case 2:
            # destructor
            if self.mtokens[mt_idx].token == self.mtokens[mt_idx - 2].token:
              mt_type = MetaTokenType.DESTRUCTOR_LIKE
            # not a valid destructor
            else:
              mt_idx -= 1
              continue
          case 3:
            # destructor
            if (self.mtokens[mt_idx - 1].token == self.mtokens[mt_idx - 4].token and
              self.mtokens[mt_idx].token == self.mtokens[mt_idx - 3].token):
              mt_type = MetaTokenType.DESTRUCTOR_LIKE
            # not a valid destructor
            else:
              mt_idx -= 1
              continue
          case 4:
            mt_type = MetaTokenType.OPERATOR_LIKE
          case 5:
            mt_type = MetaTokenType.REGULAR_LIKE
          case 6:
            mt_type = MetaTokenType.REGULAR_LIKE
          case _:
            raise Exception(f"Unimplemented structural pattern {pattern_idx}")

        # update result mtokens
        result.insert(mt_idx + 1, MetaToken(value, mt_type))
        for idx in range(0, len(pattern) + matched_qual + matched_posttempl):
          result.pop(mt_idx - idx)

        mt_idx = len(result) - 1
      
    # try joining regulars on leftover scope res operators
    for idx in range(len(result)):
      if idx + 2 < len(result):
        if (result[idx].type == MetaTokenType.REGULAR_LIKE and
            result[idx + 1].type == MetaTokenType.SCOPE_RES and 
            result[idx + 2].type == MetaTokenType.REGULAR_LIKE):
          # join regulars into a larger regular
          value = result[idx].token + result[idx + 1].token + result[idx + 2].token
          result.insert(idx, MetaToken(value, MetaTokenType.REGULAR_LIKE))
          # 1st regular
          result.pop(idx + 1)
          # ::
          result.pop(idx + 1)
          # 2nd regular
          result.pop(idx + 1)
      else:
        break

    return result

  def make_paths(self) -> List[MetaToken]:
    """Creates `PATH_LIKE` metatokens."""
    result = self.mtokens
    index = 0

    while index < len(result) - 1:
      # starting with names
      if result[index].type == MetaTokenType.REGULAR_LIKE:
        # Windows paths
        if result[index + 1].type in [MetaTokenType.BACKSLASH, MetaTokenType.DBACKSLASH]:
          path_begin = index
          path = []

          while index < len(result):
            if result[index].type in PATHLIKE_TYPES:
              path.append(result[index])
              index += 1
            else:
              break

          # join path mtokens into path-like
          value = ""
          for mt in path:
            value += mt.token

          result.insert(path_begin, MetaToken(value, MetaTokenType.PATH_LIKE))
          for idx in range(len(path)):
            result.pop(path_begin + 1)

          # restore the index
          index = path_begin + 1

        # Other paths
        elif result[index + 1].type == MetaTokenType.SLASH:
          path_begin = index
          path = []

          while index < len(result):
            if result[index].type in PATHLIKE_TYPES:
              path.append(result[index])
              index += 1
            else:
              break
          
          # join path mtokens into path-like
          value = ""
          for mt in path:
            value += mt.token

          result.insert(path_begin, MetaToken(value, MetaTokenType.PATH_LIKE))
          for idx in range(len(path)):
            result.pop(path_begin + 1)

          # restore the index
          index = path_begin + 1
            
        else:
          index += 1

      # starting with (double) backslash (Windows)
      elif result[index].type in [MetaTokenType.BACKSLASH, MetaTokenType.DBACKSLASH]:
        # Windows paths
        if result[index + 1].type == MetaTokenType.REGULAR_LIKE:
          path_begin = index
          path = []

          while index < len(result):
            if result[index].type in PATHLIKE_TYPES:
              path.append(result[index])
              index += 1
            else:
              break

          # join path mtokens into path-like
          value = ""
          for mt in path:
            value += mt.token

          result.insert(path_begin, MetaToken(value, MetaTokenType.PATH_LIKE))
          for idx in range(len(path)):
            result.pop(path_begin + 1)

          # restore the index
          index = path_begin + 1
          
        else:
          index += 1

      # starting with slash (non-Windows)
      elif result[index].type == MetaTokenType.SLASH:
        if result[index + 1].type == MetaTokenType.REGULAR_LIKE:
          path_begin = index
          path = []

          while index < len(result):
            if result[index].type in PATHLIKE_TYPES:
              path.append(result[index])
              index += 1
            else:
              break

          # join path mtokens into path-like
          value = ""
          for mt in path:
            value += mt.token

          result.insert(path_begin, MetaToken(value, MetaTokenType.PATH_LIKE))
          for idx in range(len(path)):
            result.pop(path_begin + 1)

          # restore the index
          index = path_begin + 1

        else:
          index += 1
    
      else:
        index += 1

    # join space-separated path-likes
    idx = 0
    while idx < len(result):
      # join space-separated
      if result[idx].type == MetaTokenType.PATH_LIKE:
        if (idx < len(result) - 2 and
            result[idx + 1].type == MetaTokenType.SPACE and
            result[idx + 2].type in [MetaTokenType.PATH_LIKE, MetaTokenType.REGULAR_LIKE]):
          value = result[idx].token + result[idx + 1].token + result[idx + 2].token
          result.insert(idx, MetaToken(value, MetaTokenType.PATH_LIKE))
          # 1st path-like
          result.pop(idx + 1)
          # space
          result.pop(idx + 1)
          # 2nd path-like
          result.pop(idx + 1)
          continue
        elif (idx < len(result) - 1 and result[idx + 1].type == MetaTokenType.PATH_LIKE):
          value = result[idx].token + result[idx + 1].token
          result.insert(idx, MetaToken(value, MetaTokenType.PATH_LIKE))
          # 1st path-like
          result.pop(idx + 1)
          # 2nd path-like
          result.pop(idx + 1)
          continue
          
      # join space-separated
      elif result[idx].type == MetaTokenType.REGULAR_LIKE:
        if (idx < len(result) - 2 and
            result[idx + 1].type == MetaTokenType.SPACE and
            result[idx + 2].type == MetaTokenType.PATH_LIKE):
          value = result[idx].token + result[idx + 1].token + result[idx + 2].token
          result.insert(idx, MetaToken(value, MetaTokenType.PATH_LIKE))
          # 1st path-like
          result.pop(idx + 1)
          # space
          result.pop(idx + 1)
          # 2nd path-like
          result.pop(idx + 1)
          continue
      idx += 1
    
    # join windows drive prefix and neighbour slashes
    idx = 0
    while idx < len(result):
      if result[idx].type == MetaTokenType.REGULAR_LIKE:
        if (idx < len(result) - 2 and
            result[idx + 1].type == MetaTokenType.COLON and
            result[idx + 2].type == MetaTokenType.PATH_LIKE):
          value = result[idx].token + result[idx + 1].token + result[idx + 2].token
          result.insert(idx, MetaToken(value, MetaTokenType.PATH_LIKE))
          # 1st path-like
          result.pop(idx + 1)
          # space
          result.pop(idx + 1)
          # 2nd path-like
          result.pop(idx + 1)

      # prepend slashes to neighbouring path-likes
      elif result[idx].type in [MetaTokenType.SLASH, MetaTokenType.BACKSLASH, MetaTokenType.DBACKSLASH]:
        if (idx < len(result) - 1 and
            result[idx + 1].type == MetaTokenType.PATH_LIKE):
          value = result[idx].token + result[idx + 1].token 
          result.insert(idx, MetaToken(value, MetaTokenType.PATH_LIKE))
          # slash
          result.pop(idx + 1)
          # path-like
          result.pop(idx + 1)

      # append slashes to neighbouring path-likes
      elif result[idx].type == MetaTokenType.PATH_LIKE:
        if (idx < len(result) - 1 and
            result[idx + 1].type in [MetaTokenType.SLASH, MetaTokenType.BACKSLASH, MetaTokenType.DBACKSLASH]):
          value = result[idx].token + result[idx + 1].token 
          result.insert(idx, MetaToken(value, MetaTokenType.PATH_LIKE))
          # path-like
          result.pop(idx + 1)
          # slash
          result.pop(idx + 1)

      idx += 1

    return result

  def split(self) -> List[MetaToken]:
    """Removes unused special characters and tokens."""
    joined = self.mtokens
    result = []

    # join `OTHER` tokens with neighbours
    idx = 0
    while idx < len(joined):
      if(joined[idx].type == MetaTokenType.OTHER):
        # join with left neighbour
        if (idx > 0 and 
            idx < len(joined) and 
            joined[idx - 1].type not in NON_JOINABLE and
            joined[idx - 1].token[len(joined[idx - 1].token) - 1] != ">"):
          joined[idx - 1].token += joined[idx].token
          joined[idx - 1].type = MetaTokenType.UNDEFINED
          joined.pop(idx)
        # join with right neighbour
        elif (idx + 1 < len(joined) and 
              joined[idx + 1].type not in NON_JOINABLE and
              joined[idx + 1].token[len(joined[idx + 1].token) - 1] != ">"):
          joined[idx].token += joined[idx + 1].token
          joined[idx].type = MetaTokenType.UNDEFINED
          joined.pop(idx + 1)
        # change type
        else:
          joined[idx].type = MetaTokenType.UNDEFINED
      else:
        idx += 1

    # join `UNDEFINED` tokens
    idx = 0
    
    while idx < len(joined) - 1:
      # left join
      if(joined[idx + 1].type == MetaTokenType.UNDEFINED and 
         joined[idx].type not in NON_JOINABLE and
         joined[idx].token[len(joined[idx].token) - 1] != ">"
        ):
        joined[idx].token += joined[idx + 1].token
        joined[idx].type = MetaTokenType.UNDEFINED
        joined.pop(idx + 1)
      # right join
      elif (joined[idx].type == MetaTokenType.UNDEFINED and 
         joined[idx + 1].type not in NON_JOINABLE
        ):
        joined[idx + 1].token = joined[idx].token + joined[idx + 1].token
        joined[idx + 1].type = MetaTokenType.UNDEFINED
        joined.pop(idx)
      else:
        idx += 1

    # handle simple path-like false positives due to \r, \n and \t
    idx = 0
    while idx < len(joined):
      mt = joined[idx]
      if mt.type == MetaTokenType.BACKSLASH and idx + 1 < len(joined):
        if joined[idx + 1].token in ["r", "n", "t"]:
          joined.pop[idx]
          joined.pop[idx]
          continue

      # fix path-likes
      retokenized = []
      if mt.type == MetaTokenType.PATH_LIKE:
        mt.token =  Tokenizer.__remove_eols(mt.token)
        retokenized = Tokenizer.__retokenize(mt)

        joined.pop(idx)
        for id in range(len(retokenized)):
          m = retokenized[id]
          joined.insert(idx+id, m)

      if len(retokenized) > 0:
        idx += len(retokenized)
      else:
        idx += 1

    for mt in joined:
      match mt.type:
        case (
        MetaTokenType.IDENTIFIER_LIKE |
        MetaTokenType.REGULAR_LIKE | 
        MetaTokenType.PATH_LIKE | 
        MetaTokenType.CONSTRUCTOR_LIKE |
        MetaTokenType.DESTRUCTOR_LIKE | 
        MetaTokenType.OPERATOR_LIKE | 
        MetaTokenType.OPERATOR_ID | 
        MetaTokenType.OPERATOR | 
        MetaTokenType.TEMPLATE_LIKE | 
        MetaTokenType.NUMBER_LIKE |
        MetaTokenType.NEW | 
        MetaTokenType.DELETE):
          result.append(mt)
        # ignore other mtokens
        case _:
          continue

    return result

  def __remove_eols(string: str) -> str:
    """Removes `\\r`, `\\n` and `\\t` characters from the beginning and end of a string."""
    while len(string) > 1:
      if string[0] == "\\" and string[1] in ["r", "n", "t"]:
        string = string[2:]
      elif string[len(string) - 2] == "\\" and string[len(string) - 1] in ["r", "n", "t"]:
        string = string[:-2]
      else:
        return string
      
    return string

  def __retokenize(mt: MetaToken) -> List[MetaToken]:
    """Tokenizes a false positive path-like."""
    result = []
    split = mt.token.split(" ")

    for s in split:
      if s != "":
        result.append(MetaToken(s, MetaTokenType.IDENTIFIER_LIKE))
    return result

def tokenize(string: str, lexer: Lexer, preparser: PreParser, tokenizer: Tokenizer) -> List[MetaToken]:
  """High-level tokenizer API function."""
  lexer.reset(string)
  # create metatokens
  metatokens = lexer.metatokens()
  preparser.reset(metatokens)
  # join operator metatokens into operator identifiers
  metatokens = preparser.make_operator_ids()
  preparser.reset(metatokens)
  # create template-like tokens
  metatokens = preparser.make_templates()
  tokenizer.reset(metatokens)
  # create full function name tokens
  metatokens = tokenizer.match_patterns()
  tokenizer.reset(metatokens)
  # create paths to reduce the number of tokens
  metatokens = tokenizer.make_paths()
  tokenizer.reset(metatokens)
  # split on unused meta tokens
  return tokenizer.split()
