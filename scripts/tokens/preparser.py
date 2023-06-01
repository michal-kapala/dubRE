from .lexer import MetaToken, MetaTokenType
from enum import Enum
from typing import List

INVALID_TEMPLATE_MTOKENS = [
  MetaTokenType.EXCLAMATION,
  MetaTokenType.DOT,
  MetaTokenType.TILDA,
  MetaTokenType.OPERATOR,
  MetaTokenType.OPERATOR_ID,
  MetaTokenType.EQUALS,
  MetaTokenType.PLUS,
  MetaTokenType.HYPHEN,
  MetaTokenType.SLASH,
  MetaTokenType.BACKSLASH,
  MetaTokenType.COLON,
  MetaTokenType.SEMICOLON,
  MetaTokenType.QUESTION,
  MetaTokenType.PIPE,
  MetaTokenType.PERCENT,
  MetaTokenType.CARET,
  MetaTokenType.BACKTICK,
  MetaTokenType.NEW,
  MetaTokenType.DELETE,
  MetaTokenType.AT,
  MetaTokenType.HASH,
  MetaTokenType.DOLLAR,
  MetaTokenType.RIGHT_CURLY,
  MetaTokenType.LEFT_CURLY,
  MetaTokenType.QUOTE,
  MetaTokenType.DQUOTE,
  MetaTokenType.DEST_SCOPE_RES,
  MetaTokenType.OTHER
]
"""Metatokens invalid inside of a template argument list literal."""

class OperatorType(Enum):
  NEW = 0
  """`operator new`"""
  DELETE = 1
  """`operator delete`"""
  ASSIGN = 2
  """`operator =`"""
  RSHIFT = 3
  """`operator >>`"""
  LSHIFT = 4
  """`operator <<`"""
  NOT = 5
  """`operator !`"""
  EQUAL_TO = 6
  """`operator ==`"""
  NOT_EQUAL_TO = 7
  """`operator !=`"""
  SUBSCRIPT = 8
  """`operator []`"""
  ARROW = 9
  """`operator ->`"""
  STAR = 10
  """`operator *`"""
  INCREMENT = 11
  """`operator ++`"""
  DECREMENT = 12
  """`operator --`"""
  SUBTRACT = 13
  """`operator -`"""
  ADD = 14
  """`operator +`"""
  BIT_AND = 15
  """`operator &`"""
  STRUCT_DEREF = 16
  """`operator ->*`"""
  DIV = 17
  """`operator /`"""
  MOD = 18
  """`operator %`"""
  LESS_THAN = 19
  """`operator <`"""
  LESS_THAN_EQ = 20
  """`operator <=`"""
  GT_THAN = 21
  """`operator >`"""
  GT_THAN_EQ = 22
  """`operator >=`"""
  COMMA = 23
  """`operator ,`"""
  FUNC_CALL = 24
  """`operator ()`"""
  BIT_NOT = 25
  """`operator ~`"""
  BIT_XOR = 26
  """`operator ^`"""
  BIT_OR = 27
  """`operator |`"""
  AND = 28
  """`operator &&`"""
  OR = 29
  """`operator ||`"""
  MULT_ASSIGN = 30
  """`operator *=`"""
  ADD_ASSIGN = 31
  """`operator +=`"""
  SUB_ASSIGN = 32
  """`operator -=`"""
  DIV_ASSIGN = 33
  """`operator /=`"""
  MOD_ASSIGN = 34
  """`operator %=`"""
  RSHIFT_ASSIGN = 35
  """`operator >>=`"""
  LSHIFT_ASSIGN = 36
  """`operator <<=`"""
  BIT_AND_ASSIGN = 37
  """`operator &=`"""
  BIT_OR_ASSIGN = 38
  """`operator |=`"""
  BIT_XOR_ASSIGN = 39
  """`operator ^=`"""
  NEW_ARRAY = 40
  """`operator new[]`"""
  DELETE_ARRAY = 41
  """`operator delete[]`"""
  UNKNOWN = 42
  """Unknown operator or regular text match."""

class PreParser:
    """Joins metatokens into potentially semantically meaningful tokens."""
    def __init__(self, metatokens: List[MetaToken]) -> None:
        self.mtokens = metatokens
        self.pos = 0

    def current(self) -> MetaToken:
      """Returns currently processed metatoken."""
      if self.pos >= len(self.mtokens):
        return None
      return self.mtokens[self.pos]
    
    def next(self) -> MetaToken | None:
      """Returns next metatoken or `None` if end of list was reached."""
      if self.next_pos() == None:
        return None
      return self.mtokens[self.pos + 1]

    def next_pos(self) -> int | None:
      """Returns next position or `None` if end of list was reached."""
      if self.pos + 1 >= len(self.mtokens):
        return None
      return self.pos + 1
    
    def next_next(self):
      """Returns the metatoken after next metatoken or `None` if end of list was reached."""
      if self.pos + 2 >= len(self.mtokens):
        return None
      return self.mtokens[self.pos + 2]
    
    def left(self) -> int:
      """Returns number of unprocessed metatokens."""
      return len(self.mtokens) - self.pos

    def consume(self) -> MetaToken:
      """Returns and consumes the current metatoken."""
      self.pos += 1
      return self.mtokens[self.pos - 1]

    def reset(self, new_mtokens: List[MetaToken]) -> None:
      """Reinitializes parser with a new metatoken list."""
      self.mtokens = new_mtokens
      self.pos = 0

    def empty(self) -> bool:
      """Checks if there are metatokens left for processing."""
      return self.pos == len(self.mtokens)
    
    def make_operator_ids(self) -> List[MetaToken]:
      """Creates `OPERATOR_ID` metatokens."""
      mtokens = []
      while not self.empty():
        cur = self.current()
        if cur == None:
          break
        match cur.type:
          # operators
          case MetaTokenType.OPERATOR:
            # consume "operator" keyword
            keyword = self.consume()
            cur = self.current()
            # check for space between keyword and operator
            space = None
            if not self.empty() and cur.type == MetaTokenType.SPACE:
              space = self.consume()
            # try parsing an operator name
            if not self.empty():
              # look forward for the operator symbol
              optype = self.try_parse_operator()
              mt1 = mt2 = mt3 = None

              # consume operator metatokens, join them into token(s)
              match optype:
                # 1 mtoken-long operators

                case OperatorType.NEW | OperatorType.DELETE:
                  # operator new
                  # operator delete
                  # space is required for `new` and `delete`
                  value = keyword.token + space.token + self.consume().token
                  mtokens.append(MetaToken(value, MetaTokenType.OPERATOR_ID))

                case (
                OperatorType.ASSIGN |
                OperatorType.ADD |
                OperatorType.SUBTRACT |
                OperatorType.DIV |
                OperatorType.MOD |
                OperatorType.STAR |
                OperatorType.NOT |
                OperatorType.COMMA |
                OperatorType.BIT_AND |
                OperatorType.BIT_NOT |
                OperatorType.BIT_OR |
                OperatorType.BIT_XOR |
                OperatorType.LESS_THAN |
                OperatorType.GT_THAN):
                  mt1 = self.consume()
                  space_val = space.token if space != None else ""
                  value = keyword.token + space_val + mt1.token
                  mtokens.append(MetaToken(value, MetaTokenType.OPERATOR_ID))

                # 2 mtokens-long operators

                case (
                OperatorType.RSHIFT |
                OperatorType.LSHIFT |
                OperatorType.EQUAL_TO |
                OperatorType.NOT_EQUAL_TO |
                OperatorType.AND |
                OperatorType.OR |
                OperatorType.SUBSCRIPT |
                OperatorType.FUNC_CALL |
                OperatorType.ARROW |
                OperatorType.INCREMENT |
                OperatorType.DECREMENT |
                OperatorType.LESS_THAN_EQ |
                OperatorType.GT_THAN_EQ |
                OperatorType.MULT_ASSIGN |
                OperatorType.ADD_ASSIGN |
                OperatorType.SUB_ASSIGN |
                OperatorType.DIV_ASSIGN |
                OperatorType.MOD_ASSIGN |
                OperatorType.BIT_AND_ASSIGN |
                OperatorType.BIT_OR_ASSIGN |
                OperatorType.BIT_XOR_ASSIGN):
                  mt1 = self.consume()
                  mt2 = self.consume()
                  space_val = space.token if space != None else ""
                  value = keyword.token + space_val + mt1.token + mt2.token
                  mtokens.append(MetaToken(value, MetaTokenType.OPERATOR_ID))

                # 3 mtokens-long operators

                case OperatorType.STRUCT_DEREF | OperatorType.RSHIFT_ASSIGN | OperatorType.LSHIFT_ASSIGN:
                  # operator ->*
                  # operator >>=
                  # operator <<=
                  mt1 = self.consume()
                  mt2 = self.consume()
                  mt3 = self.consume()
                  space_val = space.token if space != None else ""
                  value = keyword.token + space_val + mt1.token + mt2.token + mt3.token
                  mtokens.append(MetaToken(value, MetaTokenType.OPERATOR_ID))

                case OperatorType.NEW_ARRAY | OperatorType.DELETE_ARRAY:
                  # operator new[]
                  # operator delete[]
                  mt1 = self.consume()
                  mt2 = self.consume()
                  mt3 = self.consume()
                  # space required
                  value = keyword.token + space.token + mt1.token + mt2.token + mt3.token
                  mtokens.append(MetaToken(value, MetaTokenType.OPERATOR_ID))

                # default (not an operator)
                case OperatorType.UNKNOWN:
                  # only re-add keyword (and space if consumed) as separate tokens
                  keyword.type = MetaTokenType.IDENTIFIER_LIKE
                  mtokens.append(keyword)
                  if(space != None):
                    mtokens.append(space)
                  
            # keyword at the end of string, add as an indentifier-like (and optional space)
            else:
              keyword.type = MetaTokenType.IDENTIFIER_LIKE
              mtokens.append(keyword)
              if(space != None):
                mtokens.append(space)

          case _:
            mtokens.append(self.consume())

      return mtokens

    def get_rangle_pos(self, index: int) -> int:
      """Returns the index of the next `>` mtoken, searching right-to-left from `index`."""
      while index >= 0:
          if self.mtokens[index].type == MetaTokenType.RIGHT_ANGLE:
            return index
          index -= 1
      return -1

    def make_templates(self) -> List[MetaToken]:
      """Creates `TEMPLATE_LIKE` metatokens."""
      result = self.mtokens
      index = len(self.mtokens) - 1
      
      while index >= 0:
        right_pos = self.get_rangle_pos(index)

        # no templating (no > or not enough space to close the template expr)
        if right_pos <= 1:
          break

        # template args literal mtokens, stored in reverse order
        templ_mtokens = [self.mtokens[right_pos]]

        # try parsing args literal
        expr_depth = 1
        # skip tokens outside of the scope (and first >)
        index = right_pos - 1

        while index >= 0 and expr_depth > 0:
          match self.mtokens[index].type:
            # scope tokens
            case MetaTokenType.LEFT_ANGLE:
              templ_mtokens.append(self.mtokens[index])
              expr_depth -= 1
              if expr_depth == 0:
                break
            case MetaTokenType.RIGHT_ANGLE:
              templ_mtokens.append(self.mtokens[index])
              expr_depth += 1
            case _:
              templ_mtokens.append(self.mtokens[index])
          index -= 1

        # reverse the template-like mtokens
        templ_mtokens.reverse()

        # check if parse failed (should begin with <)
        if templ_mtokens[0].type != MetaTokenType.LEFT_ANGLE:
          # not a template literal (end of string)
          # bring position back to the token in front of failed `>` and try other `>`
          index = right_pos - 1
          continue

        # check for invalid template arg list characters/sequences
        invalid = False
        for mt in templ_mtokens:
          if mt.type in INVALID_TEMPLATE_MTOKENS:
            invalid = True
            break
          
        if invalid == True:
          continue

        # valid template literal, join mtokens
        value = ""
        for tmt in templ_mtokens:
          value += tmt.token

        # insert new and delete the old
        result.insert(right_pos + 1, MetaToken(value, MetaTokenType.TEMPLATE_LIKE))
        for idx in range(0, len(templ_mtokens)):
          result.pop(right_pos - idx)

      return result

    def try_parse_one_token_op(self) -> OperatorType:
      """Look forward for a one-mtoken long operator."""
      mtoken = self.current()
      match mtoken.type:

        # valid single mtoken operators
        case MetaTokenType.LEFT_ANGLE:
          return OperatorType.LESS_THAN
        
        case MetaTokenType.RIGHT_ANGLE:
          return OperatorType.GT_THAN
        
        case MetaTokenType.TILDA:
          return OperatorType.BIT_NOT
        
        case MetaTokenType.COMMA:
          return OperatorType.COMMA
        
        case MetaTokenType.EQUALS:
          return OperatorType.ASSIGN
        
        case MetaTokenType.PLUS:
          return OperatorType.ADD
        
        case MetaTokenType.HYPHEN:
          return OperatorType.SUBTRACT
        
        case MetaTokenType.STAR:
          return OperatorType.STAR
        
        case MetaTokenType.SLASH:
          return OperatorType.DIV
        
        case MetaTokenType.EXCLAMATION:
          return OperatorType.NOT
        
        case MetaTokenType.AND:
          return OperatorType.BIT_AND
        
        case MetaTokenType.PIPE:
          return OperatorType.BIT_OR
        
        case MetaTokenType.PERCENT:
          return OperatorType.MOD
        
        case MetaTokenType.CARET:
          return OperatorType.BIT_XOR
        
        case MetaTokenType.NEW:
          return OperatorType.NEW
        
        case MetaTokenType.DELETE:
          return OperatorType.DELETE

        # regular text match or unknown/non-existent/non-overloadable operator
        case MetaTokenType.IDENTIFIER_LIKE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SCOPE_RES:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SPACE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.OPERATOR:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DOT:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_PARENTH:
          return OperatorType.UNKNOWN 
        
        case MetaTokenType.RIGHT_PARENTH:
          return OperatorType.UNKNOWN 
        
        case MetaTokenType.BACKSLASH:
          return OperatorType.UNKNOWN

        case MetaTokenType.COLON:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SEMICOLON:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.QUESTION:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_SQUARE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_SQUARE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.QUOTE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DQUOTE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.BACKTICK:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.AT:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.HASH:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DOLLAR:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_CURLY:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_CURLY:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DEST_SCOPE_RES:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.OTHER:
          return OperatorType.UNKNOWN

    def try_parse_two_token_op(self) -> OperatorType:
      """Look forward for <= 2 mtokens-long operator."""
      mtoken = self.current()
      match mtoken.type:
        # valid double mtoken operators
        case MetaTokenType.LEFT_PARENTH:
          if self.next().type == MetaTokenType.RIGHT_PARENTH:
            # ()
            return OperatorType.FUNC_CALL
          else:
            return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_SQUARE:
          if self.next().type == MetaTokenType.RIGHT_SQUARE:
            # []
            return OperatorType.SUBSCRIPT
          else:
            return OperatorType.UNKNOWN

        # valid double and single mtoken operators
        case MetaTokenType.LEFT_ANGLE:
          match self.next().type:
            # <<
            case MetaTokenType.LEFT_ANGLE:
              return OperatorType.LSHIFT
            # <=
            case MetaTokenType.EQUALS:
              return OperatorType.LESS_THAN_EQ
            # < (single)
            case MetaTokenType.SPACE:
              return OperatorType.LESS_THAN
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_ANGLE:
          match self.next().type:
            # >>
            case MetaTokenType.LEFT_ANGLE:
              return OperatorType.RSHIFT
            # >=
            case MetaTokenType.EQUALS:
              return OperatorType.GT_THAN_EQ
            # > (single)
            case MetaTokenType.SPACE:
              return OperatorType.GT_THAN
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.EQUALS:
          match self.next().type:
            # ==
            case MetaTokenType.EQUALS:
              return OperatorType.EQUAL_TO
            # = (single)
            case MetaTokenType.SPACE:
              return OperatorType.ASSIGN
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.PLUS:
          match self.next().type:
            # ++
            case MetaTokenType.PLUS:
              return OperatorType.INCREMENT
            # +=
            case MetaTokenType.EQUALS:
              return OperatorType.ADD_ASSIGN
            # + (single)
            case MetaTokenType.SPACE:
              return OperatorType.ADD
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.HYPHEN:
          match self.next().type:
            # --
            case MetaTokenType.HYPHEN:
              return OperatorType.DECREMENT
            # -=
            case MetaTokenType.EQUALS:
              return OperatorType.SUB_ASSIGN
            # ->
            case MetaTokenType.RIGHT_ANGLE:
              return OperatorType.ARROW
            # - (single)
            case MetaTokenType.SPACE:
              return OperatorType.SUBTRACT
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.STAR:
          match self.next().type:
            # *=
            case MetaTokenType.EQUALS:
              return OperatorType.MULT_ASSIGN
            # * (single)
            case MetaTokenType.SPACE:
              return OperatorType.STAR
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.SLASH:
          match self.next().type:
            # /=
            case MetaTokenType.EQUALS:
              return OperatorType.DIV_ASSIGN
            # / (single)
            case MetaTokenType.SPACE:
              return OperatorType.DIV
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.EXCLAMATION:
          match self.next().type:
            # !=
            case MetaTokenType.EQUALS:
              return OperatorType.NOT_EQUAL_TO
            # ! (single)
            case MetaTokenType.SPACE:
              return OperatorType.NOT
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.AND:
          match self.next().type:
            # &&
            case MetaTokenType.AND:
              return OperatorType.AND
            # &=
            case MetaTokenType.EQUALS:
              return OperatorType.BIT_AND_ASSIGN
            # & (single)
            case MetaTokenType.SPACE:
              return OperatorType.BIT_AND
            case _:
              return OperatorType.UNKNOWN          
        
        case MetaTokenType.PIPE:
          match self.next().type:
            # ||
            case MetaTokenType.PIPE:
              return OperatorType.OR
            # |=
            case MetaTokenType.EQUALS:
              return OperatorType.BIT_OR_ASSIGN
            # | (single)
            case MetaTokenType.SPACE:
              return OperatorType.BIT_OR
            case _:
              return OperatorType.UNKNOWN     
        
        case MetaTokenType.PERCENT:
          match self.next().type:
            # %=
            case MetaTokenType.EQUALS:
              return OperatorType.MOD_ASSIGN
            # % (single)
            case MetaTokenType.SPACE:
               return OperatorType.MOD
            case _:
              return OperatorType.UNKNOWN
         
        case MetaTokenType.CARET:
          match self.next().type:
            # ^=
            case MetaTokenType.EQUALS:
              return OperatorType.BIT_XOR_ASSIGN
            # ^ (single)
            case MetaTokenType.SPACE:
               return OperatorType.BIT_XOR
            case _:
              return OperatorType.UNKNOWN

        # valid single mtoken operators
        case MetaTokenType.TILDA:
          if self.next().type == MetaTokenType.SPACE:
            return OperatorType.BIT_NOT
          else:
            return OperatorType.UNKNOWN
        
        case MetaTokenType.COMMA:
          if self.next().type == MetaTokenType.SPACE:
            return OperatorType.COMMA
          else:
            return OperatorType.UNKNOWN
       
        case MetaTokenType.NEW:
          if self.next().type == MetaTokenType.SPACE:
            return OperatorType.NEW
          else:
            return OperatorType.UNKNOWN
        
        case MetaTokenType.DELETE:
          if self.next().type == MetaTokenType.SPACE:
            return OperatorType.DELETE
          else:
            return OperatorType.UNKNOWN

        # regular text match or unknown/non-existent/non-overloadable operator
        case MetaTokenType.IDENTIFIER_LIKE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SCOPE_RES:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SPACE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.OPERATOR:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DOT:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_PARENTH:
          return OperatorType.UNKNOWN 
        
        case MetaTokenType.BACKSLASH:
          return OperatorType.UNKNOWN

        case MetaTokenType.COLON:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SEMICOLON:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.QUESTION:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_SQUARE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.QUOTE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DQUOTE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.BACKTICK:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.AT:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.HASH:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DOLLAR:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_CURLY:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_CURLY:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DEST_SCOPE_RES:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.OTHER:
          return OperatorType.UNKNOWN

    def try_parse_three_token_op(self) -> OperatorType:
      """Look forward for <= 3 mtokens-long operator."""
      mtoken = self.current()
      next = self.next()
      next_next = self.next_next()
      match mtoken.type:
        # valid triple, double and single mtoken operators
        case MetaTokenType.LEFT_ANGLE:
          match next.type:
            # <<
            case MetaTokenType.LEFT_ANGLE:
              match next_next.type:
                # <<=
                case MetaTokenType.EQUALS:
                  return OperatorType.LSHIFT_ASSIGN
                # << (double)
                case MetaTokenType.SPACE:
                  return OperatorType.LSHIFT
                case _:
                  return OperatorType.UNKNOWN
            # <=
            case MetaTokenType.EQUALS:
              match next_next.type:
                case MetaTokenType.SPACE:
                  return OperatorType.LESS_THAN_EQ
                case _:
                  return OperatorType.UNKNOWN
            # < (single)
            case MetaTokenType.SPACE:
              return OperatorType.LESS_THAN
            case _:
              return OperatorType.UNKNOWN
            
        # >
        case MetaTokenType.RIGHT_ANGLE:
          match next.type:
            # <<
            case MetaTokenType.RIGHT_ANGLE:
              match next_next.type:
                # >>=
                case MetaTokenType.EQUALS:
                  return OperatorType.RSHIFT_ASSIGN
                # >> (double)
                case MetaTokenType.SPACE:
                  return OperatorType.RSHIFT
                case _:
                  return OperatorType.UNKNOWN
            # >=
            case MetaTokenType.EQUALS:
              match next_next.type:
                case MetaTokenType.SPACE:
                  return OperatorType.GT_THAN_EQ
                case _:
                  return OperatorType.UNKNOWN
            # > (single)
            case MetaTokenType.SPACE:
              return OperatorType.GT_THAN
            case _:
              return OperatorType.UNKNOWN
            
        # -
        case MetaTokenType.HYPHEN:
          match next.type:
            # -- (double)
            case MetaTokenType.HYPHEN:
              match next_next.type:
                case MetaTokenType.SPACE:
                  return OperatorType.DECREMENT
                case _:
                  return OperatorType.UNKNOWN
            # -= (double)
            case MetaTokenType.EQUALS:
              match next_next.type:
                case MetaTokenType.SPACE:
                  return OperatorType.SUB_ASSIGN
                case _:
                  return OperatorType.UNKNOWN
            # ->
            case MetaTokenType.RIGHT_ANGLE:
              match next_next.type:
                # ->*
                case MetaTokenType.STAR:
                  return OperatorType.STRUCT_DEREF
                # -> (double)
                case MetaTokenType.SPACE:
                  return OperatorType.ARROW
                case _:
                  return OperatorType.UNKNOWN
            # - (single)
            case MetaTokenType.SPACE:
              return OperatorType.SUBTRACT
            case _:
              return OperatorType.UNKNOWN

        # valid triple and double mtoken operators (none)

        # valid triple and single mtoken operators
        case MetaTokenType.NEW:
          match next.type:
            # new[
            case MetaTokenType.LEFT_SQUARE:
              # new[]
              if next_next.type == MetaTokenType.RIGHT_SQUARE:
                return OperatorType.NEW_ARRAY
              else:
                return OperatorType.UNKNOWN
            # new (single)
            case MetaTokenType.SPACE:
              return OperatorType.NEW
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.DELETE:
          match next.type:
            # delete[
            case MetaTokenType.LEFT_SQUARE:
              # delete[]
              if next_next.type == MetaTokenType.RIGHT_SQUARE:
                return OperatorType.DELETE_ARRAY
              else:
                return OperatorType.UNKNOWN
            # delete (single)
            case MetaTokenType.SPACE:
              return OperatorType.DELETE
            case _:
              return OperatorType.UNKNOWN

        # valid triple operators (none)

        # valid double mtoken operators
        case MetaTokenType.LEFT_PARENTH:
          if next.type == MetaTokenType.RIGHT_PARENTH:
            # ()
            return OperatorType.FUNC_CALL
          else:
            return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_SQUARE:
          if next.type == MetaTokenType.RIGHT_SQUARE:
            # []
            return OperatorType.SUBSCRIPT
          else:
            return OperatorType.UNKNOWN

        # valid double and single mtoken operators
        case MetaTokenType.EQUALS:
          match next.type:
            # ==
            case MetaTokenType.EQUALS:
              return OperatorType.EQUAL_TO
            # = (single)
            case MetaTokenType.SPACE:
              return OperatorType.ASSIGN
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.PLUS:
          match next.type:
            # ++
            case MetaTokenType.PLUS:
              return OperatorType.INCREMENT
            # +=
            case MetaTokenType.EQUALS:
              return OperatorType.ADD_ASSIGN
            # + (single)
            case MetaTokenType.SPACE:
              return OperatorType.ADD
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.STAR:
          match next.type:
            # *=
            case MetaTokenType.EQUALS:
              return OperatorType.MULT_ASSIGN
            # * (single)
            case MetaTokenType.SPACE:
              return OperatorType.STAR
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.SLASH:
          match next.type:
            # /=
            case MetaTokenType.EQUALS:
              return OperatorType.DIV_ASSIGN
            # / (single)
            case MetaTokenType.SPACE:
              return OperatorType.DIV
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.EXCLAMATION:
          match next.type:
            # !=
            case MetaTokenType.EQUALS:
              return OperatorType.NOT_EQUAL_TO
            # ! (single)
            case MetaTokenType.SPACE:
              return OperatorType.NOT
            case _:
              return OperatorType.UNKNOWN
        
        case MetaTokenType.AND:
          match next.type:
            # &&
            case MetaTokenType.AND:
              return OperatorType.AND
            # &=
            case MetaTokenType.EQUALS:
              return OperatorType.BIT_AND_ASSIGN
            # & (single)
            case MetaTokenType.SPACE:
              return OperatorType.BIT_AND
            case _:
              return OperatorType.UNKNOWN          
        
        case MetaTokenType.PIPE:
          match next.type:
            # ||
            case MetaTokenType.PIPE:
              return OperatorType.OR
            # |=
            case MetaTokenType.EQUALS:
              return OperatorType.BIT_OR_ASSIGN
            # | (single)
            case MetaTokenType.SPACE:
              return OperatorType.BIT_OR
            case _:
              return OperatorType.UNKNOWN     
        
        case MetaTokenType.PERCENT:
          match next.type:
            # %=
            case MetaTokenType.EQUALS:
              return OperatorType.MOD_ASSIGN
            # % (single)
            case MetaTokenType.SPACE:
               return OperatorType.MOD
            case _:
              return OperatorType.UNKNOWN
         
        case MetaTokenType.CARET:
          match next.type:
            # ^=
            case MetaTokenType.EQUALS:
              return OperatorType.BIT_XOR_ASSIGN
            # ^ (single)
            case MetaTokenType.SPACE:
               return OperatorType.BIT_XOR
            case _:
              return OperatorType.UNKNOWN

        # valid single mtoken operators
        case MetaTokenType.TILDA:
          if next.type == MetaTokenType.SPACE:
            return OperatorType.BIT_NOT
          else:
            return OperatorType.UNKNOWN
        
        case MetaTokenType.COMMA:
          if next.type == MetaTokenType.SPACE:
            return OperatorType.COMMA
          else:
            return OperatorType.UNKNOWN

        # regular text match or unknown/non-existent/non-overloadable operator
        case MetaTokenType.IDENTIFIER_LIKE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SCOPE_RES:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SPACE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.OPERATOR:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DOT:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_PARENTH:
          return OperatorType.UNKNOWN 
        
        case MetaTokenType.BACKSLASH:
          return OperatorType.UNKNOWN

        case MetaTokenType.COLON:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.SEMICOLON:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.QUESTION:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_SQUARE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.QUOTE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DQUOTE:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.BACKTICK:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.AT:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.HASH:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DOLLAR:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.LEFT_CURLY:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.RIGHT_CURLY:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.DEST_SCOPE_RES:
          return OperatorType.UNKNOWN
        
        case MetaTokenType.OTHER:
          return OperatorType.UNKNOWN

    def try_parse_operator(self) -> OperatorType:
      """Returns the available operator type (`UNKNOWN` if failed)."""
      # determine match length:
      mtokens_left = self.left()
      
      # match on single mtoken ops, could be space
      if mtokens_left == 1:
        return self.try_parse_one_token_op()
      # match on [1,2]-mtoken long ops
      elif mtokens_left == 2:
        return self.try_parse_two_token_op()
      # match on [1,2,3]-mtoken long ops
      else:
        return self.try_parse_three_token_op()
 

