"""
This module implements access to the `Neo4j HTTP API <https://neo4j.com/docs/http-api/3.5/>`_ using the requests
library.
"""

import requests
import sys
from typing import List, Tuple
from collections import namedtuple


class Statement(dict):
    """Class that helps transform a cypher query plus optional parameters into the dictionary structure that Neo4j
    expects. The values can easily be accessed as shown in the last code example.

    Args:
        cypher (str): the Cypher statement
        parameters (dict): [optional] parameters that are merged into the statement at the server-side. Parameters help
            with speeding up queries because the execution plan for identical Cypher statements is cached.

    Example code:

    >>> # create simple statement
    >>> statement = Statement("MATCH () RETURN COUNT(*) AS node_count")

    >>> # create parametrized statement
    >>> statement = Statement("MATCH (n:node {uuid: {uuid}}) RETURN n", {'uuid': '123abc'})

    >>> # create multiple parametrized statements
    >>> statements = [Statement("MATCH (n:node {uuid: {uuid}}) RETURN n", {'uuid': uuid}) for uuid in ['123abc', '456def']]

    >>> # print individual Statement values
    >>> statement = Statement("MATCH (n:node {uuid: {uuid}}) RETURN n", {'uuid': '123abc'})
    >>> print("Cypher statement: {}".format(statement['statement']))
    >>> print("Parameters dict: {}".format(str(statement['parameters']))
    """

    def __init__(self, cypher: str, parameters: dict = None):
        super().__init__(statement=cypher)
        if parameters:
            self['parameters'] = parameters


class Connector:
    """Class that abstracts communication with neo4j into up-front setup and then executes one or more
    :class:`Statement`. The connector doesn't maintain an open connection and thus doesn't need to be closed after
    use.

    Args:
        endpoint (str): the fully qualified endpoint to send messages to
        credentials (tuple[str, str]): the credentials that are used to authenticate the requests
        verbose_errors (bool): if set to True the :class:`Connector` prints :class:`Neo4jErrors` messages and codes to
            the standard error output in a bit nicer format than the stack trace.

    Example code:

    >>> # default connector
    >>> connector = Connector()

    >>> # localhost connector, custom credentials
    >>> connector = Connector(credentials=('username', 'password'))

    >>> # custom connector
    >>> connector = Connector('http://mydomain:7474', ('username', 'password'))
    """

    # default endpoint of localhost
    default_host = 'http://localhost:7474'
    default_path = '/db/data/transaction/commit'

    # default credentials
    default_credentials = ('neo4j', 'neo4j')

    def __init__(self, host: str = default_host, credentials: Tuple[str, str] = default_credentials,
                 verbose_errors=False):
        self.endpoint = host + self.default_path
        self.credentials = credentials
        self.verbose_errors = verbose_errors

    def run(self, cypher: str, parameters: dict = None):
        """
        Method that runs a single statement against Neo4j in a single transaction. This method builds the
        :class:`Statement` object for the user.

        Args:
            cypher (str): the Cypher statement
            parameters (dict): [optional] parameters that are merged into the statement at the server-side. Parameters
                help with speeding up queries because the execution plan for identical Cypher statements is cached.

        Returns:
            list[dict]: a list of dictionaries, one dictionary for each row in the result. The keys in the dictionary
            are defined in the Cypher statement

        Raises:
            Neo4jErrors

        Example code:

        >>> # retrieve all nodes' properties
        >>> all_nodes = [row['n'] for row in connector.run("MATCH (n) RETURN n")]

        >>> # single row result
        >>> node_count = connector.run("MATCH () RETURN COUNT(*) AS node_count")[0]['node_count']

        >>> # get a single node's properties with a statement + parameter
        >>> # in this case we're assuming: CONSTRAINT ON (node:node) ASSERT node.uuid IS UNIQUE
        >>> single_node_properties_by_uuid = connector.run("MATCH (n:node {uuid: {uuid}}) RETURN n", {'uuid': '123abc'})[0]['n']
        """
        response = self.post([Statement(cypher, parameters)])
        return self._clean_results(response)[0]

    def run_multiple(self, statements: List[Statement], batch_size: int = None) -> List[List[dict]]:
        """
        Method that runs multiple :class:`Statement`\ s against Neo4j in a single transaction or several batches.

        Args:
            statements (list[Statement]): the statements to execute
            batch_size (int): [optional] number of statements to send to Neo4j per batch. In case the batch_size is
                omitted (i.e. None) then all statements are sent as a single batch. This parameter can help make large
                jobs manageable for Neo4j (e.g not running out of memory).

        Returns:
            list[list[dict]]: a list of statement results, each containing a list of dictionaries, one dictionary for
            each row in the result. The keys in the dictionary are defined in the Cypher statement. The statement
            results have the same order as the corresponding :class:`Statement`\ s

        Raises:
            Neo4jErrors

        Example code:

        >>> cypher = "MATCH (n:node {uuid: {uuid}}) RETURN n"
        >>> statements = [Statement(cypher, {'uuid': uuid}) for uuid in ['123abc', '456def']
        >>> statements_responses = connector.run_multiple(statements)
        >>> for statement_responses in statements_responses:
        >>>     for row in statement_responses:
        >>>         print(row)

        >>> # we can use batches if we're likely to overwhelm neo4j by sending everything in a single request
        >>> # note that this has no effect on the returned data structure
        >>> cypher = "MATCH (n:node {uuid: {uuid}}) RETURN n"
        >>> statements = [Statement(cypher, {'uuid': uuid}) for uuid in range(1_000_000)
        >>> statements_responses = connector.run_multiple(statements, batch_size=10_000)
        >>> for statement_responses in statements_responses:
        >>>     for row in statement_responses:
        >>>         print(row)

        >>> # we can easily re-use some information from the statement in the next example
        >>> cypher = "MATCH (language {name: {name}})-->(word:word)) RETURN word"
        >>> statements = [Statement(cypher, {'name': lang}) for lang in ['en', 'nl']
        >>> statements_responses = connector.run_multiple(statements)
        >>> for statement, responses in zip(statements, statements_responses):
        >>>     for row in responses:
        >>>         print("{language}: {word_lemma}".format(language=statement['parameters']['lang'], word=row['word']['lemma']))
        """
        # flatten cleaned responses from batches
        return [
            row
            for statements_batch in self.make_batches(statements, batch_size)
            for row in self._clean_results(self.post(statements_batch))
        ]

    def post(self, statements: List[Statement]):
        """
        Method that performs an HTTP POST with the provided :class:`Statement`\ s and returns the parsed data structure
        as `specified in Neo4j's documentation
        <https://neo4j.com/docs/http-api/3.5/http-api-actions/begin-and-commit-a-transaction-in-one-request/>`_.
        This specifically includes the metadata per row and has a separate entry for the result names and the actual
        values.

        Args:
            statements (list[Statement]): the statements that are POST-ed to Neo4j

        Returns:
            dict: the parsed Neo4j HTTP API response

        Raises:
            Neo4jErrors

        Example code:

        >>> cypher = "MATCH (n:node {uuid: {uuid}}) RETURN n"
        >>> statements = [Statement(cypher, {'uuid': uuid}) for uuid in ['123abc', '456def']
        >>> statements_responses = connector.run_multiple(statements)
        >>> for result in statements_responses['results']:
        >>>     for datum in result['data']:
        >>>         print(datum['row'][0]) #n is the first item in the row
        """
        response = requests.post(self.endpoint, json={'statements': statements}, auth=self.credentials)
        json_response = response.json()

        self._check_for_errors(json_response)

        return json_response

    @staticmethod
    def make_batches(statements: List[Statement], batch_size: int = None) -> List:
        # only 1 batch
        if batch_size is None:
            yield statements

        # multiple batches
        else:
            if batch_size < 1:
                raise ValueError("batchsize should be >= 1")

            for start_idx in range(0, len(statements), batch_size):
                yield statements[start_idx:start_idx + batch_size]

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
    object to get the individual :class:`Neo4jError` objects

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
