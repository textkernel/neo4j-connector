from setuptools import setup

with open('README.md') as readme_file:
    long_description = readme_file.read()

with open('requirements.txt') as requirements_file:
    install_requires = requirements_file.read()

setup(
    name='neo4j-connector',
    version='1.0.0',
    description='Single-transaction HTTP API connector for Neo4j',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Jelle Jan Bankert (Textkernel BV)',
    author_email='bankert@textkernel.com',
    url='https://github.com/textkernel/neo4j-connector',
    license='MIT',
    packages=['neo4j'],
    install_requires=install_requires,
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Database",
        "Topic :: Software Development",
        "Topic :: Utilities",
    ]
)
