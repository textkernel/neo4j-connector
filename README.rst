******
README
******

This library contains everything you need to execute single-request transactions for Neo4j 3.0 and above through its
HTTP API.

Background
==========
Research into the speed of performing ETL and batch-type actions on Neo4j showed that using a large, single-request
transaction POST-request through Neo4j's HTTP API outperforms other currently available libraries for this use-case
(e.g. the official 'neo4j-driver' and 'py2neo'). The goal of this connector is to provide convenience methods and
classes that abstract away the boilerplate communication code.

Community thread about the difference in performance between drivers:
    https://community.neo4j.com/t/barebones-http-requests-much-faster-than-python-neo4j-driver-and-py2neo

Example
=======

.. code-block:: python

    import neo4j

    connector = neo4j.Connector('http://localhost:7474', ('neo4j','neo4j'))
    response = connector.run("""MATCH () RETURN COUNT(*) as node_count""")
    first_row = response[0]
    print(first_row['node_count'])

Installation
============

To install the latest stable version, use:

.. code:: bash

    pip install neo4j-connector

Github
======

This library lives at https://github.com/textkernel/neo4j-connector. Suggestions, bug-reports and pull requests are
welcome there.

Documentation
=============

The documentation (including changelog) lives at https://neo4j-connector.readthedocs.io
