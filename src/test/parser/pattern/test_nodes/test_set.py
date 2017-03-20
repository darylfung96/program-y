from test.parser.pattern.test_nodes.base import PatternTestBaseClass
from programy.parser.pattern.nodes import *

class PatternSetNodeTests(PatternTestBaseClass):

    def test_init(self):
        node = PatternSetNode("test1")
        self.assertIsNotNone(node)

        self.assertFalse(node.is_root())
        self.assertFalse(node.is_priority())
        self.assertFalse(node.is_wildcard())
        self.assertFalse(node.is_zero_or_more())
        self.assertFalse(node.is_one_or_more())
        self.assertIsNotNone(node.children)
        self.assertFalse(node.has_children())

        self.assertTrue(node.equivalent(PatternSetNode("test1")))
        self.assertFalse(node.is_root())
        self.assertEqual(node.to_string(), "SET [P(0)^(0)#(0)C(0)_(0)*(0)To(0)Th(0)Te(0)] name=[TEST1]")
