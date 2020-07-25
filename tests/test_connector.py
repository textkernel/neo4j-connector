import neo4j
import pytest
import asyncio


class TestConnectorBasics:
    def test_basic_parameters_existence(self):
        hostname = "http://domain:7474"
        connector = neo4j.Connector(hostname)
        assert connector.endpoint.startswith(hostname)
        assert connector.endpoint.endswith(connector.default_path)
        assert connector.credentials != None
        assert connector.verbose_errors != None


class TestErrorHandling:
    def setup(self):
        self.connector = neo4j.Connector()

    def test_no_error_response(self):
        self.connector._check_for_errors({"errors": []})
        self.connector._check_for_errors({})

    def test_single_error_response(self):
        errors = [{"code": "code", "message": "message"}]

        try:
            self.connector._check_for_errors({"errors": errors})
            self.fail("Expected a raised Neo4jErrors, but didn't get one")
        except neo4j.Neo4jErrors as neo4j_errors:
            assert len(neo4j_errors.errors) == len(errors)

    def test_multiple_error_response(self):
        errors = [
            {"code": "code", "message": "message"},
            {"code": "code2", "message": "message2"},
        ]

        try:
            self.connector._check_for_errors({"errors": errors})
            self.fail("Expected a raised Neo4jErrors, but didn't get one")
        except neo4j.Neo4jErrors as neo4j_errors:
            assert len(neo4j_errors.errors) == len(errors)


class TestPostingStatements:
    cypher1 = "MERGE (a:Foo) RETURN a"
    cypher2 = "MERGE (b:Bar) RETURN b"

    def setup(self):
        self.connector = neo4j.Connector()

    def teardown(self):
        self.connector.run("MATCH (n) DELETE n")

    def test_run_single(self):
        response = self.connector.run(self.cypher1)
        row = response[0]

        assert "a" in row.keys()

    def test_run_multiple(self):
        statements = [neo4j.Statement(self.cypher1), neo4j.Statement(self.cypher2)]
        response = self.connector.run_multiple(statements)

        statement_1_first_row = response[0][0]
        assert "a" in statement_1_first_row.keys()

        statement_2_first_row = response[1][0]
        assert "b" in statement_2_first_row.keys()

    def test_run_multiple_batch(self):
        statements = [neo4j.Statement(self.cypher1), neo4j.Statement(self.cypher2)]
        response = self.connector.run_multiple(statements, batch_size=1)

        statement_1_first_row = response[0][0]
        assert "a" in statement_1_first_row.keys()

        statement_2_first_row = response[1][0]
        assert "b" in statement_2_first_row.keys()
