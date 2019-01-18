from unittest import TestCase
from neo4j import Neo4jErrors, Neo4jError


class Neo4jErrorTestCase(TestCase):
    def test_single_error(self):
        code = 'code'
        message = 'message'

        error_dicts = [{'code': code, 'message': message}]
        expected_error_obj = Neo4jError(code, message)

        neo4j_errors = Neo4jErrors(error_dicts)

        self.assertEqual(len([error for error in neo4j_errors]), len(error_dicts))
        self.assertIn(expected_error_obj, neo4j_errors)

    def test_multiple_errors(self):
        code = 'code'
        message = 'message'
        code2 = 'code2'
        message2 = 'message2'

        error_dicts = [{'code': code, 'message': message}, {'code': code2, 'message': message2}]
        expected_error_obj1 = Neo4jError(code, message)
        expected_error_obj2 = Neo4jError(code2, message2)

        neo4j_errors = Neo4jErrors(error_dicts)

        self.assertEqual(len([error for error in neo4j_errors]), len(error_dicts))
        self.assertIn(expected_error_obj1, neo4j_errors)
        self.assertIn(expected_error_obj2, neo4j_errors)
