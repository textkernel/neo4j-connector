"""Module that contains everything you need to run single-commit statements with Neo4j through the HTTP API

Research into the speed of performing batch-type actions on Neo4j showed that using a large, single-commit POST-request
through Neo4j's HTTP API outperforms other methods like utilised by 'py2neo' and the official 'neo4j-driver'. The goal
of this module is to make it easy to run one or more statements in a fast, single request.

Community thread about the difference in performance between drivers:
    https://community.neo4j.com/t/barebones-http-requests-much-faster-than-python-neo4j-driver-and-py2neo
Neo4j HTTP API specification:
    https://neo4j.com/docs/http-api/3.5/
"""

import requests
import sys
from typing import List, Tuple
from collections import namedtuple


class Statement(dict):
    """Class that helps transform a cypher query plus optional parameters into the right dictionary structure."""

    def __init__(self, cypher: str, parameters: dict = None):
        super().__init__(statement=cypher)
        if parameters:
            self['parameters'] = parameters


class Connector:
    """Class that abstracts communication with neo4j into up-front setup and then running one or more ``neo4j.Statement``.

    Args:
        endpoint (str): the fully qualified endpoint to send messages to
        credentials (tuple[str, str]): the credentials that are used to authenticate the requests
    """

    # default endpoint of localhost
    default_host = 'http://localhost:7474'
    default_path = '/db/data/transaction/commit'

    # default credentials
    default_credentials = ('neo4j', 'neo4j')

    def __init__(self, host: str = default_host, credentials: Tuple[str, str] = default_credentials,
                 verbose_errors=False):
        self.endpoint = ''.join([host, self.default_path])
        self.credentials = credentials
        self.verbose_errors = verbose_errors

    def run(self, cypher: str, parameters: dict = None):
        """
        Method that runs a single statement against Neo4j in a single transaction. This method builds the Statement
        object for the user.

        Args:
            cypher (str): the Cypher statement
            parameters (dict): [optional] parameters that are merged into the statement at the server-side

        Returns:
            list[dict]: a list of dictionaries, one dictionary for each row in the result. The keys in the dictionary
            are defined in the Cypher statement

        Raises:
            Neo4jErrors

        Example code:

        >>> # retrieve all nodes' properties
        >>> all_nodes = [row['n'] for row in run("MATCH (n) RETURN n")]

        >>> # single row result
        >>> node_count = run("MATCH () RETURN COUNT(*) AS node_count")[0]['node_count']

        >>> # get a single node's properties with a statement + parameter
        >>> # in this case we're assuming: CONSTRAINT ON (node:node) ASSERT node.uuid IS UNIQUE
        >>> single_node_properties_by_uuid = run("MATCH (n:node {uuid: {uuid}}) RETURN n", {'uuid': '123abc'})[0]['n']
        """
        response = self.post([Statement(cypher, parameters)])
        return self._clean_results(response)[0]

    def run_multiple(self, statements: List[Statement]):
        """
        Method that runs multiple statements against Neo4j in a single transaction.

        Args:
            statements (list[Statement]): the Statements to run

        Returns:
            list[list[dict]]: a list of statement results, each containing a list of dictionaries, one dictionary for
            each row in the result. The keys in the dictionary are defined in the Cypher statement.

        Raises:
            Neo4jErrors

        Example code:

        >>> cypher = "MATCH (n:node {uuid: {uuid}}) RETURN n"
        >>> statements = [Statement(cypher, {'uuid': uuid}) for uuid in ['123abc', '456def']
        >>> statements_responses = run_multiple(statements)
        >>> for statement_responses in statements_responses
        >>>     for row in statement_responses
        >>>         print(row)

        """
        response = self.post(statements)
        return self._clean_results(response)

    def post(self, statements: List[Statement]):
        """
        Method that performs an HTTP POST with the provided statements and returns the parsed data structure as
        provided by Neo4j. This specifically includes the metadata per row and has a separate entry for the result
        names and the actual values.

        See the Neo4j documentation here:
        https://neo4j.com/docs/http-api/current/http-api-actions/begin-and-commit-a-transaction-in-one-request/

        Args:
            statements (list[Statement]): the statements that are POST-ed to Neo4j

        Returns:
            dict: the parsed Neo4j HTTP API response

        Raises:
            Neo4jErrors

        Example code:

        >>> cypher = "MATCH (n:node {uuid: {uuid}}) RETURN n"
        >>> statements = [Statement(cypher, {'uuid': uuid}) for uuid in ['123abc', '456def']
        >>> statements_responses = run_multiple(statements)
        >>> for result in statements_responses['results']
        >>>     for datum in result['data']
        >>>         print(datum['row'])
        """
        response = requests.post(self.endpoint, json={'statements': statements}, auth=self.credentials)
        json_response = response.json()

        self._check_for_errors(json_response)

        return json_response

    def _check_for_errors(self, json_response):
        errors = json_response.get('errors')
        if errors:
            neo4j_errors = Neo4jErrors(errors)
            if self.verbose_errors:
                for neo4j_error in neo4j_errors:
                    print(neo4j_error.code, file=sys.stderr)
                    print(neo4j_error.message, file=sys.stderr)
            raise neo4j_errors

    @staticmethod
    def _clean_results(response):
        return [
            [
                dict(zip(result['columns'], datum['row']))
                for datum in result['data']
            ]
            for result in response['results']
        ]


class Neo4jErrors(Exception):
    """Exception that is raised when Neo4j responds to a request with one or more error message. Iterate over this
    object to get the individual :class:Neo4jError objects

    Args:
        errors (list(dict)): A list of dictionaries that contain the 'code' and 'message' properties

    Example code:

    >>> try:
    >>>     connector.run(...)
    >>> except Neo4jErrors as neo4j_errors:
    >>>     for neo4j_error in neo4j_errors:
    >>>         print(neo4j_error.code, file=sys.stderr)
    >>>         print(neo4j_error.message, file=sys.stderr)
    """

    def __init__(self, errors: List[dict]):
        self.errors = [Neo4jError(error['code'], error['message']) for error in errors]

    def __iter__(self):
        return iter(self.errors)


# wrapped the namedtuple in a class so it gets documented properly
class Neo4jError(namedtuple('Neo4jError', ['code', 'message'])):
    """namedtuple that contains the code and message of a Neo4j error

    Args:
        code (str): Error status code as defined in https://neo4j.com/docs/status-codes/3.5/
        message (str): Descriptive message. For Cypher syntax errors this will contain a separate line (delimited by \\\\n)
            that contains the '^' character to point to the problem

    Example code:

    >>> print(neo4j_error.code, file=sys.stderr)
    >>> print(neo4j_error.message, file=sys.stderr)
    """
