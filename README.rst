***************
Neo4j Connector
***************

This library contains everything you need to run single-commit statements with Neo4j 3.0 and above through the HTTP API.

Background
============
Research into the speed of performing batch-type actions on Neo4j showed that using a large, single-commit POST-request
through Neo4j's HTTP API outperforms other methods like utilised by 'py2neo' and the official 'neo4j-driver'. The goal
of this connector is to make it easy to run one or more statements in a fast, single request.

Community thread about the difference in performance between drivers:
    https://community.neo4j.com/t/barebones-http-requests-much-faster-than-python-neo4j-driver-and-py2neo

Example
========
.. code-block:: python
    from neo4j-connector import neo4j
    connector = neo4j.Connector('')
    response = connector.run("""MATCH () RETURN COUNT(*) as node_count""")
    first_row = response[0]
    print(first_row['node_count'])

Installation
============

To install the latest stable version, use:

.. code:: bash
    pip install neo4j-connector