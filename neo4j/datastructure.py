__author__ = 'Tomer'

CORPUS_ROOT = "C:\\temp\\switchboard-nxt-release-1.0\\switchboard-nxt-release-1.0"

from py2neo import Graph, Node, Relationship, authenticate

class Neo4JGraph():
    def __init__(self,username,password):
        self.username = username
        self.password = password
        self.graph    = None

    def connect(self):
        url = 'http://localhost:7474'
        if self.username and self.password:
             authenticate(url.strip('http://'), self.username, self.password)
        self.graph = Graph(url + '/db/data/')

    def get_graph(self):
        return self.graph

    def clean(self):
        query="""
            start n=node(*)
            match n-[r]-()
            delete n,r
            """
        self.graph.cypher.execute(query)

        query ="""start n=node(*)
                match n
                delete n"""

        self.graph.cypher.execute(query)

