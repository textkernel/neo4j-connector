from unittest import TestCase, mock
import neo4j


class ConnectorBasicsTestCase(TestCase):
    def test_basic_parameters_existence(self):
        hostname = 'http://domain:7474'
        connector = neo4j.Connector(hostname)
        self.assertTrue(connector.endpoint.startswith(hostname))
        self.assertTrue(connector.endpoint.endswith(connector.default_path))
        self.assertIsNotNone(connector.credentials)
        self.assertIsNotNone(connector.verbose_errors)


class ErrorHandlingTestCase(TestCase):
    def setUp(self):
        self.connector = neo4j.Connector()

    def test_no_error_response(self):
        self.connector._check_for_errors({'errors': []})
        self.connector._check_for_errors({})

    def test_single_error_response(self):
        errors = [
            {'code': 'code', 'message': 'message'}
        ]

        try:
            self.connector._check_for_errors({
                'errors': errors
            })
            self.fail("Expected a raised Neo4jErrors, but didn't get one")
        except neo4j.Neo4jErrors as neo4j_errors:
            self.assertEqual(len(neo4j_errors.errors), len(errors))

    def test_multiple_error_response(self):
        errors = [
            {'code': 'code', 'message': 'message'},
            {'code': 'code2', 'message': 'message2'}
        ]

        try:
            self.connector._check_for_errors({
                'errors': errors
            })
            self.fail("Expected a raised Neo4jErrors, but didn't get one")
        except neo4j.Neo4jErrors as neo4j_errors:
            self.assertEqual(len(neo4j_errors.errors), len(errors))


def mock_requests_post(*args, **kwargs):
    # Inspired by https://stackoverflow.com/a/28507806/803466

    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    def get_results(statement_ids):
        return [{
            'columns': [
                f'key-{id}'
            ],
            'data': [
                {
                    'row': [f'value-{id}'],
                    'meta': [f'meta-{id}']
                }
            ]
        } for id in statement_ids]

    statements = [statement_obj['statement'] for statement_obj in kwargs['json']['statements']]
    return MockResponse({'results': get_results(statements), 'errors': []}, 200)


class PostingStatementsTestCase(TestCase):
    cypher1 = 'cypher-1'
    cypher2 = 'cypher-2'

    def setUp(self):
        self.connector = neo4j.Connector()

    @mock.patch('neo4j.requests.post', side_effect=mock_requests_post)
    def test_post(self, mock_get):
        hostname = 'hostname'
        credentials = ('username', 'password')

        connector = neo4j.Connector(hostname, credentials)
        connector.post([neo4j.Statement(self.cypher1)])

        expected_endpoint = hostname + connector.default_path

        mock_get.assert_called_once_with(expected_endpoint, auth=credentials,
                                         json={'statements': [{'statement': self.cypher1}]})

    @mock.patch('neo4j.requests.post', side_effect=mock_requests_post)
    def test_run_single(self, mock_get):
        response = self.connector.run(self.cypher1)
        row = response[0]
        self.assertEqual(row['key-cypher-1'], 'value-cypher-1')

    @mock.patch('neo4j.requests.post', side_effect=mock_requests_post)
    def test_run_multiple(self, mock_get):
        statements = [neo4j.Statement(self.cypher1), neo4j.Statement(self.cypher2)]
        response = self.connector.run_multiple(statements)

        statement_1_first_row = response[0][0]
        self.assertEqual(statement_1_first_row['key-cypher-1'], 'value-cypher-1')

        statement_2_first_row = response[1][0]
        self.assertEqual(statement_2_first_row['key-cypher-2'], 'value-cypher-2')
