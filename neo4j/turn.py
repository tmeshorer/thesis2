__author__ = 'Tomer'



import xmltodict
import os
from py2neo import Node, Relationship
import json
import logging
from   pandas import *
logger = logging.getLogger('curpus')


def create_href(fname,nite_id):
    return fname + "#id(" + nite_id + ")"


#---------------------------------------- Turns file ---------------------------------------------
  #<turn nite:id="t1" nite:start="0.8" nite:end="10.85" approx="false">
  #    <nite:child href="sw2005.A.syntax.xml#id(s1)..id(s2)"/>
  # </turn>

class TurnDir():
    def __init__(self,path):
        self.path = path
        self.dialogs = {}
        self.all_turns = []

    def read(self,dialog_node):
        logger.info("enter terminal dir for %s " % dialog_node.id)
        for i in os.listdir(self.path):
            parts = i.split('.')
            dialog_id = parts[0]
            speaker_id= parts[1]
            if dialog_node.get_sw_id() == dialog_id:
                f = TurnFile(self.path +"\\" + i,dialog_id,speaker_id,i)
                turn_list = f.read()
                for t in turn_list:
                    self.all_turns.append(t)

                if not dialog_id in self.dialogs:
                    self.dialogs[dialog_id] = {}
                speakers_in_dialogs = self.dialogs[dialog_id]
                speakers_in_dialogs[speaker_id] = turn_list
                logger.info("read turns files %s " % dialog_id)

    def as_data_frame(self):
        return DataFrame(self.all_turns)

class TurnFile():
    def __init__(self,path,dialog_id,speaker_id,fname):
        self.dialog_id = dialog_id
        self.speaker_id = speaker_id
        self.path = path
        self.fname = fname

    def read(self):
        logger.info("enter terminal file for %s " % self.dialog_id)
        
        result = []
        with open(self.path) as fd:
              obj = xmltodict.parse(fd.read())
              for x in obj["nite:turn_stream"]["turn"]:
                    t = TurnRelation(self.dialog_id,self.speaker_id,self.fname)
                    t.read(x)
                    result.append(t)
        return result


class TurnRelation():
    def __init__(self,dialog_id,speaker_id,fname):
        self.speaker_id = speaker_id
        self.dialog_id = dialog_id
        self.id = None
        self.start = None
        self.end  = None
        self.start_id = None
        self.end_id = None
        self.child = None
        self.href = None
        self.fname = fname
        self.from_parse_href = None
        self.to_parse_href = None

        # used during parsing
        self.from_parse = None
        self.to_parse = None

        # start time point
        self.start_time_point = None
        self.end_time_poinr = None

        #indicate turn change
        self.turn_change = False


    def read(self,m):
        try:
            self.id       = m["@nite:id"]
            if "@nite:start" in m:
                self.start    = float(m['@nite:start'])
            if "@nite:end" in m:
                self.end      = float(m['@nite:end'])
            if "@approx" in m:
                self.approx   = m["@approx"]
            self.child    = m["nite:child"]["@href"]
            if '..' in self.child:
                 #<nite:child href="sw2005.A.syntax.xml#id(s40)..id(s41)"/>
                 parts = self.child.split('..')
                 parts_2 = parts[0].split('#')
                 href1 = parts[0]
                 href2 = parts_2[0]+'#'+parts[1]
                 self.from_parse_href = href1
                 self.to_parse_href   = href2
            else:
                self.from_parse_href = self.child
            self.href = create_href(self.fname,self.id)
        except:
            raise Exception(json.dumps(m,indent=4))

    def get_start_time(self):
        if self.start == None:
            self.start = self.from_parse.get_start_time()
        return self.start

    def get_end_time(self):
        if (self.end == None):
            if self.to_parse == None:
                self.end = self.from_parse.get_end_time()
            else:
                self.end = self.to_parse.get_end_time()
        return self.end

    def __str__(self):
        return "Turn(%s %s, %s %s, : from %s to %s)" % (self.id,
                                                        self.dialog_id,
                                                        self.speaker_id,
                                                        self.id,
                                                        self.get_start_time(),
                                                        self.get_end_time())

    def as_dict(self):
        result = {}
        result['id'] = self.id
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['start']   = self.get_start_time()
        result['end']   = self.get_end_time()
        result['fname'] = self.fname
        return result




    def resolve_parse(self,dialog):
        logger.info("resolving parse for turn %s " % self.href)
     
        if self.from_parse_href != None:
            self.from_parse = dialog.find_parse_by_href(self.from_parse_href)
            if self.from_parse == None:
                raise "cannot find from prase %s" % self.from_parse_href
        if self.to_parse_href != None:
            self.to_parse = dialog.find_parse_by_href(self.to_parse_href)
            if self.to_parse == None:
                raise "cannot find to prase %s" % self.to_parse_href
    

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p


class OpenFloorRelation():
    def __init__(self,dialog_id):
        self.dialog_id = dialog_id
        self.start = None
        self.end  = None


        # start time point
        self.start_time_point = None
        self.end_time_poinr = None

    def get_start_time(self):
        return self.start

    def get_end_time(self):
        return self.end

    def __str__(self):
        return "OpenFloor(%s, from: %s to: %s)" % (self.dialog_id,self.start, self.end)

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p

