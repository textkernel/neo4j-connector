from unittest import TestCase
from neo4j import Statement


class StatementTestCase(TestCase):
    cypher = 'cypher'
    params = {'key': 'value'}

    def test_cypher_no_params(self):
        statement = Statement(self.cypher)

        self.assertEqual(len(statement), 1)

        self.assertIn('statement', statement)
        self.assertEqual(statement['statement'], self.cypher)

    def test_cypher_with_params(self):
        statement = Statement(self.cypher, self.params)
        self.assertEqual(len(statement), 2)

        self.assertIn('statement', statement)
        self.assertEqual(statement['statement'], self.cypher)

        self.assertIn('parameters', statement)
        self.assertEqual(statement['parameters'], self.params)
