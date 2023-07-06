import unittest
from tokens.lexer import Lexer, MetaToken, MetaTokenType
from tokens.preparser import PreParser
from tokens.tokenizer import Tokenizer, tokenize


class TestCase(unittest.TestCase):

  def test_operator(self):
    input = "TIndexedContainerIterator<TArray<TScriptDelegate<FWeakObjectPtr>,TSizedInlineAllocator<4,32,TSizedDefaultAllocator<32> > > const ,TScriptDelegate<FWeakObjectPtr> const ,int>::operator->"
    expected = [MetaToken(input, MetaTokenType.OPERATOR_LIKE)]
    result = tokenize(input, Lexer(""), PreParser([]), Tokenizer([]))
    self.assertEqual(len(result), len(expected))

    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)

  def test_constructor(self):
    input = "oo2::vector_flex<unsigned __int64,oo2::vector_storage_a<unsigned __int64> >::vector_flex<unsigned __int64,oo2::vector_storage_a<unsigned __int64> >"
    expected = [MetaToken(input, MetaTokenType.CONSTRUCTOR_LIKE)]
    result = tokenize(input, Lexer(""), PreParser([]), Tokenizer([]))
    self.assertEqual(len(result), len(expected))
    
    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)

  def test_destructor(self):
    input = "oo2net::vector_storage<oo2net::rated_packet>::~vector_storage<oo2net::rated_packet>"
    expected = [MetaToken(input, MetaTokenType.DESTRUCTOR_LIKE)]
    result = tokenize(input, Lexer(""), PreParser([]), Tokenizer([]))
    self.assertEqual(len(result), len(expected))
    
    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)

  def test_regular(self):
    input = "TSparseDynamicDelegate<FActorBeginOverlapSignature_MCSignature,AActor,FActorBeginOverlapSignatureInfoGetter>::Add"
    expected = [MetaToken(input, MetaTokenType.REGULAR_LIKE)]
    result = tokenize(input, Lexer(""), PreParser([]), Tokenizer([]))
    self.assertEqual(len(result), len(expected))
    
    for idx in range(len(expected)):
      self.assertEqual(result[idx].token, expected[idx].token)
      self.assertEqual(result[idx].type, expected[idx].type)


if __name__ == '__main__':
  unittest.main()
