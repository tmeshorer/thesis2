__author__ = 'Tomer'


import xmltodict
import os
import json
from py2neo import Node, Relationship
import logging
from pandas import *
logger = logging.getLogger('curpus')


def create_href(fname,nite_id):
    return fname + "#id(" + nite_id + ")"



#---------------------------------------- Dialog act file ------------------------------------------

#<da niteType="statement" swbdType="sd" nite:id="da42">
#<nite:child href="sw2005.A.terminals.xml#id(s36_1)"/>
#<nite:child href="sw2005.A.terminals.xml#id(s36_3)"/>
#<nite:child href="sw2005.A.terminals.xml#id(s36_5)"/>
#<nite:child href="sw2005.A.terminals.xml#id(s36_7)"/>
#</da>

class DialogActDir():
    def __init__(self,path):
        self.path = path
        self.dialogs = {}
        self.all_dacts = []

    def read(self,dialog_node):
        logger.info("enter Dialog Act Dir for %s " % dialog_node)
        for i in os.listdir(self.path):
            parts = i.split('.')
            dialog_id = parts[0]
            speaker_id= parts[1]
            if dialog_node.get_sw_id() == dialog_id:
                f = DialogActFile(self.path + "\\" + i,dialog_id,speaker_id,i)
                dial_act_relations = f.read()

                if not dialog_id in self.dialogs:
                    self.dialogs[dialog_id] = {}
                speakers_in_dialogs = self.dialogs[dialog_id]
                speakers_in_dialogs[speaker_id] = dial_act_relations
                logger.info("read dial act files %s " % dialog_node)



class DialogActFile():
    def __init__(self,path,dialog_id,spaker_id,fname):
        self.dialog_id = dialog_id
        self.speaker_id = spaker_id
        self.path = path
        self.fname = fname


    def read(self):
        logger.info("enter DialogActFile::read %s " % self.dialog_id)
        
        result = []
        with open(self.path) as fd:
              obj = xmltodict.parse(fd.read())
              for x in obj["nite:dialAct_stream"]["da"]:
                    da = DialogActRelation(self.dialog_id,self.speaker_id,self.fname)
                    da.read(x)
                    result.append(da)
        return result

class DialogActRelation():

    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id =dialog_id
        self.speaker_id =speaker_id
        self.fname = fname
        self.id = id
        self.terminals_href = []
        self.terminals = []

        # start time point
        self.start_time_point = None
        self.end_time_poinr = None

        # artifical start and stop. In case where the dacts does not have any terminals
        self.virtual_start = 0
        self.virtual_end = 0        

    def get_start_time(self):
        if self.size() == 0:
            return self.virtual_start   
        return self.terminals[0].get_start_time()

    def get_end_time(self):
        if self.size() == 0:
            return self.virtual_end
        return self.terminals[-1].get_end_time()

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p

    def size(self):
        return len(self.terminals)


    # <da niteType="open_q" swbdType="qo" nite:id="da2">
    # <nite:child href="sw2005.A.terminals.xml#id(s2_1)"/>
    def read(self,m):
        try :
            self.id = m["@nite:id"]
            self.href = create_href(self.fname,self.id)
            self.swbdType = m["@swbdType"]
            self.niteType = m["@niteType"]
            child_obj = m["nite:child"]
            #for each_child in m["nite:child"]["@href"]:
            if isinstance(child_obj,dict):
                term_id = child_obj["@href"]
                self.terminals_href.append(term_id)
            if isinstance(child_obj,list):
                for x in child_obj:
                    term_id = x["@href"]
                    self.terminals_href.append(term_id)


        except:
            raise Exception(json.dumps(m,indent=4))


    def find(self):
        t = self.graph.get_graph().find_one("DialogAct", "href", self.href)
        return t
    def __str__(self):
        return "DialAct(%s, %s %s, : from %s to %s)" % (self.dialog_id,self.speaker_id,self.id,self.get_start_time(), self.get_end_time())

    def resolve_terminals(self,dialog):
        # do the actual terminals
        for each_id in self.terminals_href:
            terminal = dialog.find_terminal(each_id)
            if terminal != None:
                self.terminals.append(terminal)

    def as_dict(self):
        result = {}
        result['id'] = self.id
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['start']   = self.get_start_time()
        result['end']   = self.get_end_time()
        result['fname'] = self.fname
        result['swbdType'] = self.swbdType
        result['niteType'] = self.niteType
        return result
