import unittest
from typing import List
from tokens.lexer import Lexer, MetaToken, MetaTokenType
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer


class TestCase(unittest.TestCase):

  def test_operator(self):
    input = "TIndexedContainerIterator<TArray<TScriptDelegate<FWeakObjectPtr>,TSizedInlineAllocator<4,32,TSizedDefaultAllocator<32> > > const ,TScriptDelegate<FWeakObjectPtr> const ,int>::operator->"
    expected = [MetaToken(input, MetaTokenType.OPERATOR_LIKE)]
    result = test(input)
    self.assertEqual(len(result), len(expected))

    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)

  def test_constructor(self):
    input = "oo2::vector_flex<unsigned __int64,oo2::vector_storage_a<unsigned __int64> >::vector_flex<unsigned __int64,oo2::vector_storage_a<unsigned __int64> >"
    expected = [MetaToken(input, MetaTokenType.CONSTRUCTOR_LIKE)]
    result = test(input)
    self.assertEqual(len(result), len(expected))
    
    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)

  def test_destructor(self):
    input = "oo2net::vector_storage<oo2net::rated_packet>::~vector_storage<oo2net::rated_packet>"
    expected = [MetaToken(input, MetaTokenType.DESTRUCTOR_LIKE)]
    result = test(input)
    self.assertEqual(len(result), len(expected))
    
    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)

  def test_regular(self):
    input = "TSparseDynamicDelegate<FActorBeginOverlapSignature_MCSignature,AActor,FActorBeginOverlapSignatureInfoGetter>::Add"
    expected = [MetaToken(input, MetaTokenType.REGULAR_LIKE)]
    result = test(input)
    self.assertEqual(len(result), len(expected))
    
    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)


def test(input: str) -> List[MetaToken]:
  lex = Lexer(input)
  metatokens = lex.metatokens()
  parser = PreParser(metatokens)
  metatokens = parser.make_operator_ids()
  parser.reset(metatokens)
  metatokens = parser.make_templates()
  tokenizer = Tokenizer(metatokens)
  metatokens = tokenizer.match_patterns()
  tokenizer.reset(metatokens)
  metatokens = tokenizer.make_paths()
  tokenizer.reset(metatokens)
  return tokenizer.split()

if __name__ == '__main__':
  unittest.main()
