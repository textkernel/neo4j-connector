from unittest import TestCase
from neo4j import Neo4jError


class Neo4jErrorTestCase(TestCase):
    def test_neo4j_error(self):
        code = 'code'
        message = 'message'

        error = Neo4jError(code, message)

        self.assertEqual(error.code, code)
        self.assertEqual(error.message, message)
