__author__ = 'Tomer'


import xmltodict
import os
import json
from py2neo import Node, Relationship
from pandas import *

import logging
logger = logging.getLogger('curpus')



def create_href(fname,nite_id):
    return fname + "#id(" + nite_id + ")"

class SyntaxDir():
    def __init__(self,path):
        self.path = path
        self.dialogs = {}
        self.all_parse = []
        

    def read(self,dialog_node):
        logger.info("enter Syntax Dir for %s " % dialog_node)
        for i in os.listdir(self.path):
            parts = i.split('.')
            dialog_id  = parts[0]
            speaker_id = parts[1]

            if dialog_node.get_sw_id() == dialog_id:
                f = SyntaxFile(self.path+"\\"+i,i,dialog_id,speaker_id)
                trees = f.read()

                for p in trees:
                    self.all_parse.append(p)
        
                if not dialog_id in self.dialogs:
                    self.dialogs[dialog_id] = {}
                speakers_in_dialogs = self.dialogs[dialog_id]
                speakers_in_dialogs[speaker_id] = trees

                logger.info("read syntax files %s " % dialog_id)


#    def recurse_add_nt(self,parent):
#         for x in parent.nt_relations:
#             self.all_nt.append(x.as_dict())
#             self.recurse_add_nt(x)

    def all_parse_data_frame(self):
        return DataFrame(self.all_parse)

    def all_nt_data_frame(self):
        return DataFrame(self.all_nt)


class SyntaxFile():
    def __init__(self,path,fname,dialog_id,speaker_id):
        self.dialog_id = dialog_id
        self.speaker_id = speaker_id
        self.path = path
        self.fname = fname

    def read(self):
        result = []
        with open(self.path) as fd:
              obj = xmltodict.parse(fd.read())
              for x in obj["nite:parse_stream"]["parse"]:
                    p = ParseRelation(self.dialog_id,self.speaker_id,self.fname)
                    p.read(x)
                    result.append(p)
        return result

class ParseRelation():
    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id = dialog_id
        self.speaker_id = speaker_id
        self.fname = fname
        self.id = None
        self.nt_relations = []
        self.start_time_point = None
        self.end_time_point = None

    def __str__(self):
        return "Parse %s %s %s , %s %s" % (
            self.id,
            self.dialog_id,
            self.speaker_id,
            self.get_start_time(),
            self.get_end_time())

    def as_dict(self):
        result = {}
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['txt'] = self.txt
        result['start'] = self.get_start_time()
        result['end']   = self.get_end_time()
        result['fname'] = self.fname
        return result


    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p

    def resolve_terminals(self,dialog):
        for nt in self.nt_relations:
            nt.resolve_terminals(dialog)

    def find(self):
        t = self.graph.get_graph().find_one("Parse", "href", self.href)
        return t


    def read(self,json_dict):
        self.id = json_dict["@nite:id"]
        self.href = create_href(self.fname,self.id)
        # parse the nt
       # print json.dumps(json_dict,indent=4)
        # if x is a dict\
        if "nt" in json_dict:
            if isinstance(json_dict["nt"], dict):
                child = NonTerminalRelation(self.dialog_id,self.speaker_id,self.fname)
                child.read(json_dict["nt"])
                self.nt_relations.append(child)
            elif isinstance(json, list):
                for each in json_dict["nt"]:
                    child = NonTerminalRelation(self.dialog_id,self.speaker_id,self.fname)
                    child.read(each)
                    self.nt_relations.append(child)
        return self.nt_relations

    def add_nt(self,nt):
        self.nt_relations.append(nt)

    def get_start_time(self):
            return self.nt_relations[0].get_start_time()

    def get_end_time(self):
            return self.nt_relations[-1].get_end_time()


"""
"@nite:start": "485.354750",
                "@nite:end": "490.882000",
                "@cat": "VP",
                "@nite:id": "s185_503",
                "@wc": "12",
                "nite:child": {
                    "@href": "sw2028.A.terminals.xml#id(s185_6)"
                },
                "nt": {
                    "@nite:start": "485.524750",
                    "@nite:end": "490.882000",
                    "@cat": "VP",
                    "@nite:id": "s185_504",
                    "@wc": "11",
                    "nite:child": {
                        "@href": "sw2028.A.terminals.xml#id(s185_7)"
                    },
                    "nt": {
                        "@nite:start": "485.784750",
"""


class NonTerminalRelation():
    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id =dialog_id
        self.speaker_id = speaker_id
        self.id = None
        self.fname = fname
        self.start = None
        self.end   = None
        self.wc    = None
        self.cat   = None
        self.terminal_ids  = []# the terminal for this non terminal
        self.terminals = []
        self.nt_relations = []    # the list of non terminals
        self.start_time_point = None
        self.end_time_point = None

    def __str__(self):
        return "%s %s %s, %s - %s, %s " % (self.dialog_id,
                                           self.speaker_id,
                                           self.id,
                                           self.start,
                                           self.end,
                                           self.cat)



    def as_dict(self):
        result = {}
        result['type'] = "sil"
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['wc'] = self.wc
        result['cat'] = self.cat
        result['terminals'] = len(self.terminal_ids)
        result['nts'] = len(self.nt_relations)
        result['start']   = self.get_start_time()
        result['end']   = self.get_end_time()
        result['fname'] = self.fname
        return result


    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p

    def resolve_terminals(self,dialog):
        for nt in self.nt_relations:
            nt.resolve_terminals(dialog)
        # do the actual terminals
        for each_id in self.terminal_ids:
            terminal = dialog.find_terminal(each_id)
            self.terminals.append(terminal)

    def get_start_time(self):
        # if the start time is ?, try to get the start time of the first terminal
        if self.start != "?":
            return float(self.start)
        else:
            if len(self.terminals) == 0 or self.terminals[0] ==None:
                return None
            return self.terminals[0].get_start_time()

    def get_end_time(self):
        # if the start time is ?, try to get the start time of the first terminal
        if self.end != "?":
            return float(self.end)
        else:
            if len(self.terminals) == 0 or self.terminals[0] ==None or self.terminals[1] ==None:
                return None
            if len(self.terminals) == 1:
                return self.terminals[0].get_end_time()
            if len(self.terminals) == 2:
                return self.terminals[1].get_end_time()


    def find(self):
        t = self.graph.get_graph().find_one("NonTerminal", "href", self.href)
        return t


    def read(self,json_dict):
        try :
            self.start = json_dict["@nite:start"]
            self.end   = json_dict["@nite:end"]
            self.cat   = json_dict["@cat"]
            self.id    = json_dict["@nite:id"]
            self.href  = create_href(self.fname,self.id)
        except:
            raise Exception(json.dumps(json_dict,indent=4))

        if "@subcat" in json_dict:
            self.subcat = json_dict["@subcat"]
        if "@wc" in json_dict:
            self.wc     = json_dict["@wc"]
        if "nite:child" in json_dict:
            # the direct terminal children
            if  "nite:child" in json_dict:
                #if this dict
                if isinstance(json_dict["nite:child"], dict):
                       self.terminal_ids.append( json_dict["nite:child"]["@href"])
                else:
                    for y in json_dict["nite:child"]:
                       self.terminal_ids.append( y["@href"])

        if "nt" in json_dict:
            # the non terminal attribute
            if isinstance(json_dict["nt"], dict):
                child = NonTerminalRelation(self.dialog_id,self.speaker_id,self.fname)
                child.read(json_dict["nt"])
                self.nt_relations.append(child)
            elif isinstance(json, list):
                for each in json_dict["nt"]:
                    child = NonTerminalRelation(self.dialog_id,self.speaker_id,self.fname)
                    child.read(each)
                    self.nt_relations.append(child)

    def add_non_terminal(self,t):
        self.non_terminals.append(t)

