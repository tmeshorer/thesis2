__author__ = 'Tomer'



import xmltodict
import os
import json
from py2neo import Graph, Node, Relationship, authenticate
from datastructure import Graph
from corpus import *
import pandas as pd

import logging
logger = logging.getLogger('curpus')


FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
invalid_logger = logging.getLogger('invalid')
invalid_logger.setLevel(logging.DEBUG)



# add log file
invalid_hdlr = logging.FileHandler('c:\\temp\\invalid.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
invalid_hdlr.setFormatter(formatter)
invalid_logger.addHandler(invalid_hdlr) 


# ---------------- Neo4J Graph -------------------

def create_href(fname,nite_id):
    return fname + "#id(" + nite_id + ")"

class CorpusResourcesDir():
        def __init__(self,path):
            self.path = path
            self.speakers = None
            self.topics   = None
            self.dialogs  = None
            self.all_speaker = []
            self.all_topics  = []
            self.all_dialogs = []

        def read(self):
            """
            Read all the corpus files and init
            :return:
            """
            sf = SpeakerFile(os.path.join(self.path,"speakers.xml"))
            self.speakers = sf.read()

            for x in self.speakers:
                self.all_speaker.append(x.as_dict())

            tf = TopicFile(os.path.join(self.path,"topics.xml"))
            self.topics = tf.read()

            for x in self.topics:
                self.all_topics.append(x.as_dict())

            tf = DialogFile(os.path.join(self.path,"dialogues.xml"))
            self.dialogs = tf.read()

            for x in self.dialogs:
                self.all_dialogs.append(x.as_dict())

            
        def speakers_df(self):
           return pd.DataFrame(self.all_speakers)

        def topcis_df(self):
            return pd.DataFrame(self.all_topics)
       
        def dialogs_df(self):
           return pd.DataFrame(self.all_dialogs)
       



# ---------------------------- Speaker File ---------------------------------------
#  <speaker nite:id="spkr1000" sex="F" dob="1954" dialect="SOUTH"/>
class SpeakerFile():
    def __init__(self,path):
        self.path = path

    def read(self):
        """
        :return: a list of speakers
        """
        result = []
        with open(self.path) as fd:
                obj = xmltodict.parse(fd.read())
                for x in obj["nite:speaker_stream"]["speaker"]:
                    s = SpeakerNode("speakers.xml")
                    s.parse(x)
                    result.append(s)
        return result



class SpeakerNode() :
    # <speaker nite:id="spkr1000" sex="F" dob="1954" dialect="SOUTH"/>
    def __init__(self,fname):
        self.id  = None
        self.sex = None
        self.dob = None
        self.dialect = None
        self.fname = fname

    def parse(self,json_dict):
        self.id      = json_dict['@nite:id']
        self.sex     = json_dict['@sex'],
        self.dob     = json_dict['@dob']
        self.dialect = json_dict['@dialect']
        self.href    = create_href(self.fname,self.id)

    def as_dict(self):
         result = {}
         result['id']        = self.id
         result['sex']       = self.sex
         result['dob']       = self.dob
         result['dialect']   = self.dialect
         result['href']      = self.href
         return result



    def find(self):
        speaker = self.graph.get_graph().find_one("Speaker", "href", self.href)
        return speaker

    def register(self):
        if not self.find():
            speaker = Node("Speaker", id=self.id,href=self.href,dob=self.dob)
            self.graph.get_graph().create(speaker)
            return True
        else:
            return False



# ---------------------------- Dialog File ---------------------------------------

class DialogFile():
    def __init__(self,path):
        self.path = path

    def read(self):
        result = []
        with open(self.path) as fd:
                obj = xmltodict.parse(fd.read())
                for x in obj["nite:dialogue_stream"]["dialogue"]:
                    d = DialogueNode("dialogues.xml")
                    d.parse(x)
                    result.append(d)
        return result

#<dialogue nite:id="dial2005" swbdid="2005">
#  <nite:pointer href="topics.xml#id(top305)" role="topic"/>
#  <nite:pointer href="speakers.xml#id(spkr1169)" role="A"/>
#  <nite:pointer href="speakers.xml#id(spkr1133)" role="B"/>
#</dialogue>

class DialogueNode():
     def __init__(self,fname):
         self.id = None
         self.swbdid = None
         self.topic_id = None
         self.A_id = None
         self.B_id = None
         self.A = None  #speaker A
         self.B = None  #speaker B
         self.href = None
         self.fname = fname
         self.timeline = None

         # the data structure that each dialog holds
         self.terminals = []
         self.turns     = []
         self.parses    = []
         self.dialacts  = []
         self.timepoints = [] # the dialog time line

     def find_terminal(self,terminal_href):
         for t in self.terminals:
             if (t.href == terminal_href):
                 return t
         # at this point the terminal was not found, print all the terminals
         logger.info("terminal not found at dialog %s " % self.id) 
         logger.info("number of terminals %s " % len(self.terminals)) 
         #raise Exception("Terminal " + terminal_href + " not found in dialog " + self.id)
         invalid_logger.info("Terminal " + terminal_href + " not found in dialog " + self.id)
         return None

     def find_parse_by_href(self,parse_href):
         for p in self.parses:
             if (p.href == parse_href):
                 return p
         raise Exception("Parse " + parse_href + " not found in dialog " + self.id)


     def find(self):
         return self.graph.get_graph().find_one("Dialogue","href",self.href)

     def register(self):
         if not self.find():
                dialogue = Node("Dialogue",id=self.id,swbid=self.swbdid,href=self.href)
                self.graph.get_graph().create(dialogue)
                return True
         else:
                return False


     def register_relationships(self):
          speaker_A = self.graph.get_graph().find_one("Speaker", "href", self.A_id)
          speaker_B = self.graph.get_graph().find_one("Speaker", "href", self.B_id)
          topic     = self.graph.get_graph().find_one("Topic", "href", self.topic_id)

          rel = Relationship(self.find(), "A", speaker_A)
          self.graph.get_graph().create(rel)
          rel = Relationship(self.find(), "B", speaker_B)
          self.graph.get_graph().create(rel)
          rel = Relationship(self.find(), "TOPIC", topic)
          self.graph.get_graph().create(rel)


     def parse(self,m):
         self.id       = m['@nite:id']
         self.swbdid   = m["@swbdid"]
         self.topic_id = m['nite:pointer'][0]['@href']
         self.A_id     = m['nite:pointer'][1]['@href']
         self.B_id     = m['nite:pointer'][2]['@href']
         self.href    = create_href(self.fname,self.id)

     def as_dict(self):
         result = {}
         result['id']     = self.id
         result['swbdid'] = self.swbdid
         result['A_id']   = self.A_id
         result['B_id']   = self.B_id
         result['href']   = self.href
         return result

     def resolve(self):
         self.A = SPEAKERS[self.A_id]
         self.B = SPEAKERS[self.B.id]

     def get_A(self):
         return self.A

     def get_B(self):
         return self.B

     def add_turn_stream(self, turn_stream):
          rel = Relationship(self.find(), "TURNS", turn_stream.find())
          self.graph.get_graph().create(rel)

     def add_dialact_stream(self, dialact_stream):
         rel = Relationship(self.find(), "DIAL_ACTS", dialact_stream.find())
         self.graph.get_graph().create(rel)

     def add_terminal_stream(self, terminal_stream):
         rel = Relationship(self.find(), "TERMINALS", terminal_stream.find())
         self.graph.get_graph().create(rel)

     def add_parse_stream(self, parse_stream):
         rel = Relationship(self.find(), "PARSE_TREES", parse_stream.find())
         self.graph.get_graph().create(rel)

     def get_sw_id(self):
         return self.id.replace("dial","sw") 


#----------------------------------------------------------------------------------------------------
# ---------------------------- Topic File -----------------------------------------------------------
#----------------------------------------------------------------------------------------------------


#<topic nite:id="top304"
#    abstract="CREDIT CARD USE"
#    question="PLEASE DISCUSS CREDIT CARDS.  FIND OUT HOW THE OTHER CALLER MAKES USE OF CREDIT CARDS.  HOW DO THEY COMPARE TO YOUR OWN?"/>

class TopicFile():
    def __init__(self,path):
        self.path = path

    def read(self):
        """
        Read all the topics
        :return: the list of topics
        """
        result = []
        with open(self.path) as fd:
                obj = xmltodict.parse(fd.read())
                for x in obj["nite:topic_stream"]["topic"]:
                    t = TopicNode("topics.xml")
                    t.parse(x)
                    result.append(t)
        return result

class TopicNode():
    def __init__(self,fname):
        self.id = None
        self.abstract = None
        self.question = None
        self.fname = fname
        self.href  = None

    def parse(self,m):
        self.id       = m['@nite:id']
        self.abstract = m['@abstract']
        self.question = m['@question']
        self.href     = create_href(self.fname,self.id)

    def find(self):
        topic = self.graph.get_graph().find_one("Topic", "href", self.href)
        return topic

    def as_dict(self):
        result = {}
        result['id'] = self.id
        result['abstract'] = self.abstract
        result['question'] = self.question
        result['href']     = self.href
        return result

