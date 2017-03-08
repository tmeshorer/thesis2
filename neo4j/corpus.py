__author__ = 'Tomer'

######
# Todo:
#     0) debug and create the graph
#     1) Add speaker relation, which include all the time that the speaker
#     speak
#     2) Add sooe;mce relation concontabie nodes that are connecited.
#     3) Add punc.
#     3) List all the long reach variable
#     4) compute the long reach variable per each turn end.
#########
import sys
import xmltodict
import os
import json
import logging
import shutil
from py2neo import Graph, Node, Relationship, authenticate
from datastructure import Graph
from corpus_resources import *
from terminal import TerminalDir,WordRelation,adj_start_and_time,PuncRelation,SilRelation,TraceRelation
from syntax import SyntaxDir,ParseRelation, NonTerminalRelation
from turn import TurnDir,TurnRelation,OpenFloorRelation
from dialact import DialogActDir,DialogActRelation
from datastructure import Neo4JGraph

from itertools import chain
from operator import attrgetter
import query
import pandas as pd

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('curpus')
logger.setLevel(logging.INFO)
error_log = logging.getLogger('error')
error_log.setLevel(logging.INFO)



# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# add the handlers to the logger
logger.addHandler(ch)

# add log file
hdlr = logging.FileHandler('c:\\temp\\sb.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 

#set the error log
ehdlr = logging.FileHandler('c:\\temp\\rejected_dialogs.log')
eformatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
ehdlr.setFormatter(formatter)
error_log.addHandler(ehdlr) 

CORPUS_ROOT = "C:\\temp\\switchboard-nxt-release-1.0\\switchboard-nxt-release-1.0"

def start_time_compare(x,y):
       return cmp(x.get_start_time(),y.get_start_time())


def id_compare(x, y):
       x_id = x.id
       y_id = y.id
       x_parts = x_id.split("_")
       y_parts = y_id.split("_")
       x_s_id = x_parts[0]
       y_s_id = y_parts[0]
       if x_s_id == y_s_id:
            return cmp(int(x_parts[1]),int(y_parts[1]))
       return cmp(int(x_parts[0][1:]),int(y_parts[0][1:]))



def id_compare_pure(x_id, y_id):
       x_parts = x_id.split("_")
       y_parts = y_id.split("_")
       x_s_id = x_parts[0]
       y_s_id = y_parts[0]
       if x_s_id == y_s_id:
            return cmp(int(x_parts[1]),int(y_parts[1]))
       return cmp(int(x_parts[0][1:]),int(y_parts[0][1:]))

def parse_compare(x, y):
        if x.get_start_time() != None and y.get_start_time() != None:
           return cmp(x.get_start_time(),y.get_start_time())
        
        #take out this line once we know all the invalid dial act
        return cmp(int(x.id[1:]),int(y.id[1:]))

def turn_compare(x, y):
        if x.get_start_time() != None and y.get_start_time() != None:
           return cmp(x.get_start_time(),y.get_start_time())
        if (x.get_start_time() == None):
            print "no start time: %s" % x
        if (y.get_start_time() == None):
            print "no start time: %s" % y
        return cmp(int(x.id[1:]),int(y.id[1:]))

def dialact_compare(x, y):
        if x.size() == 0 or y.size() == 0:
            return cmp(int(x.id[2:]),int(y.id[2:]))
        if x.get_start_time() != None and y.get_start_time() != None:
            return cmp(x.get_start_time(),y.get_start_time())

        return cmp(int(x.id[2:]),int(y.id[2:]))


def set_time_on_all_terminals(x):
    # build an hash table with a list for each sentence
    sentences = {}
    for t in x:
       id_parts = t.id.split("_")
       s_id = id_parts[0]
       if not s_id in sentences:
           sentences[s_id] = []
       terms = sentences[s_id]
       terms.append(t)

    # make a list of list based on the sentence key.
    # this way we assign time to sentences based on thier location, and not the
    # hash location
    keys = []
    for id,terms in sentences.iteritems():
        keys.append(id)

    sorted_keys = sorted(keys,id_compare_pure)
    sorted_sentences = []
    for key in sorted_keys:
        sorted_sentences.append(sentences[key])


     # at this point each sentence is a list of term in the hash
    i = 0
    sorted_sentences_2 = []
    for terms in sorted_sentences:
         sorted_terms = sorted(terms,id_compare)
         sorted_sentences_2.extend(sorted_terms)
         first_term = sorted_terms[0]
         if first_term.get_start_time() == None:
             #look for start time
             first_term_with_time = None
             for x in sorted_terms:
                 if x.get_start_time() != None:
                     first_term_with_time = x
                     break
             if first_term_with_time == None:
                 # we do not have time for the sentence, get the time from prev
                 # sentence end
                 first_term_s_id = int(first_term.id.split('_')[0][1:])
                 # get the prev sentence
                 prev_first_term_s_id = 's' + str(first_term_s_id - 1)
                 prev_s = sentences[prev_first_term_s_id]
                 last_term = prev_s[-1]
                 first_term.start = last_term.get_end_time()
                 first_term.end = first_term.start
             else:
                 first_term.start = first_term_with_time.start
                 first_term.end = first_term.start

         last_end_time = None
         for t in sorted_terms:
             if t.get_start_time() == None:
                 t.start = last_end_time
                 if isinstance(t,SilRelation):
                    sil_index = sorted_terms.index(t)
                    if sil_index < len(sorted_terms) - 1:
                        next_term = sorted_terms[sil_index + 1]
                        t.end = next_term.get_start_time()
                    else:
                        t.end = t.start
                 else:
                    t.end = t.start
             if (t.get_end_time() != None):
                 last_end_time = t.get_end_time()


    return sorted_sentences_2


class SbCorpus():
    def __init__(self, root_path):
        self.root_path = root_path
        self.topic_nodes = {}
        self.speaker_nodes = {}
        self.dialog_nodes = {}

    def read_dialog_data(self,dialog_node):
        self.read_terminals(dialog_node)
        self.read_syntax(dialog_node)
        self.read_turns(dialog_node)
        self.read_dacts(dialog_node)
        self.read_time_line(dialog_node)

    def read_time_line(self,dialog_node):
        logger.debug("reading timeline")
        if len(dialog_node.terminals) > 0:
                b = DialogTimelineBuilder(dialog_node)
                b.build()
                dialog_node.timeline = b.get_timeline()

        logger.debug("done reading timeline")


    def read_dacts(self, dialog_node):
        count = 0
        logger.info("enter read dacts")
        dacts = DialogActDir(os.path.join(self.root_path, "xml", "dialAct"))
        dacts.read(dialog_node)

        # for each dialog
        for key, value in dacts.dialogs.iteritems():
            logger.debug("start read all the dialact for dialog %s" % key)

            dialog = self.dialog_nodes[key.replace("sw", "dial")]

            A_acts = dacts.dialogs[key]['A']
            B_acts = dacts.dialogs[key]['B']

            A_acts.extend(B_acts)
            for x in A_acts:
                x.resolve_terminals(dialog)
            sorted_dial_acts = sorted(A_acts, cmp=dialact_compare)

            # fix the sorted dacts in case where the dact does not have start and end time
            i=0
            dial_acts_len = len(sorted_dial_acts)
            for i in range(dial_acts_len):
                if sorted_dial_acts[i].size() == 0:
                    sorted_dial_acts[i].virtual_start = sorted_dial_acts[i-1].get_end_time()
                    sorted_dial_acts[i].virtual_end   = sorted_dial_acts[i-1].get_end_time()


            # find the dialog
            dialog.dialacts = sorted_dial_acts
            logger.info("done reading dialog act for dialog %s, read :%s dial acts" % (dialog_node.id,len(dialog.dialacts)))

        

    def read_turns(self, dialog_node):
        count = 0
        logger.info("enter read turns for dialog %s",dialog_node)
        turns = TurnDir(os.path.join(self.root_path, "xml", "turns"))
        turns.read(dialog_node)
        # for each dialog
        for key, value in turns.dialogs.iteritems():
            dialog = self.dialog_nodes[key.replace("sw", "dial")]

            A_turns = turns.dialogs[key]['A']
            B_turns = turns.dialogs[key]['B']
            A_turns.extend(B_turns)
            for t in A_turns:
                t.resolve_parse(dialog)
            sorted_turns = sorted(A_turns, cmp=turn_compare)
            # find the dialog
            dialog.turns = sorted_turns

            # fix the start time and end time of turns
            for i in range(0,len(dialog.turns)):
                if dialog.turns[i].get_start_time() == None:
                    before = dialog.turns[i-1].get_end_time()
                    dialog.turns[i].start = before
                if dialog.turns[i].get_end_time() == None:
                    after = dialog.turns[i+1].get_start_time()
                    dialog.turns[i].end = after
                


            logger.debug("read all the turns for dialog %s" % key)
            logger.debug("adding the floor open for %s" % key)
            turns_with_open_floor = []
            ofloor = None
            for i in range(0, len(sorted_turns) - 1):
                current_turn = sorted_turns[i]
                next_turn = sorted_turns[i + 1]
                if current_turn.speaker_id != next_turn.speaker_id:
                    current_turn.turn_change = True

                if (current_turn.get_end_time() < next_turn.get_start_time()):
                    ofloor = OpenFloorRelation(current_turn.dialog_id)
                    ofloor.start = current_turn.get_end_time()
                    ofloor.end = next_turn.get_start_time()
                else:
                    turns_with_open_floor.append(current_turn)
                    print "Overlapp turn %s ,   with    %s" % (current_turn, next_turn)
                    continue
                turns_with_open_floor.append(current_turn)
                turns_with_open_floor.append(ofloor)
            turns_with_open_floor.append(sorted_turns[-1])
            dialog_node.turns = turns_with_open_floor
            logger.info("read turn %s " % len(dialog_node.turns))



    def read_syntax(self, dialog_node):
        logger.info("enter read syntax for dialog %s " % dialog_node)
        ts = SyntaxDir(os.path.join(self.root_path, "xml", "syntax"))
        ts.read(dialog_node)
        # for each dialog
        for key, value in ts.dialogs.iteritems():
            A_parses = ts.dialogs[key]['A']
            B_parses = ts.dialogs[key]['B']

            dialog = self.dialog_nodes[key.replace("sw", "dial")]

            # try to first resolve the terminals
            for a_p in A_parses:
                a_p.resolve_terminals(dialog)

            for b_p in B_parses:
                b_p.resolve_terminals(dialog)

            A_parses.extend(B_parses)
            sorted_parses = sorted(A_parses, cmp=parse_compare)
            # find the dialog
            dialog.parses = sorted_parses
            logger.debug("read all the syntax for dialog %s number of syntax %s" % (key,len(sorted_parses)))


        

    def read_terminals(self, dialog_node):
        logger.info("enter read terminals")
        td = TerminalDir(os.path.join(self.root_path, "xml", "terminals"))
        td.read(dialog_node)
        # for each dialog
        for key, value in td.dialogs.iteritems():
            logger.info("read all the terminals for dialog %s" % key)
            A_terminals = td.dialogs[key]['A']
            B_terminals = td.dialogs[key]['B']
            # merge both lists
            A_terminals.extend(B_terminals)
            try:
                with_time = set_time_on_all_terminals(A_terminals)
                # sorted_terminals = sorted(with_time,cmp = start_time_compare)
                for x in with_time:
                    if x.get_start_time() > x.get_end_time():
                        if x.get_end_time() == None:
                            x.end = x.start
                        else:
                            x.start = x.end
                            logger.error("invalid state %s start time > end time" % x)
                # find the dialog
                dialog = self.dialog_nodes[key.replace("sw", "dial")]
                # adj_start_and_time(sorted_terminals)
                dialog.terminals = with_time
                logger.info("read terminals %s " % len(dialog.terminals))

            except:
                e = sys.exc_info()[0]
                logger.error("error reading terminals for %s " % e)

        logger.debug("done reading terminals")


    def read_corpus_resources(self):
        logger.debug("read corpus resources")

        crd = CorpusResourcesDir(os.path.join(self.root_path, "xml", "corpus-resources"))
        crd.read()
        # read the corpus resources
        for x in crd.topics:
            self.topic_nodes[x.id] = x
        for x in crd.speakers:
            self.speaker_nodes[x.id] = x
        for x in crd.dialogs:
            self.dialog_nodes[x.id] = x

        logger.debug("done reading corpus resources " + str(len(self.dialog_nodes)))


    

class TimePoint():

    def __init__(self,v):
        self.v = float(v)
        #nodes that enter the point
        self.incoming_nodes = []
        #nodes that exit the node
        self.outgoing_nodes = []
        self.gn = None

    def set_graph_node(self,p):
        self.gn = p

    def get_graph_node(self):
        return self.gn

    def add_incoming(self,n):
        self.incoming_nodes.append(n)

    def add_outgoing(self,n):
        self.outgoing_nodes.append(n)





class DialogTimeline():
    def __init__(self):
        self.points = []
        self.last_valid_time = None

    def insert_point(self,p):
        i = 0
        for each in self.points:
            if each.v < p.v:
                i = i + 1
        self.points.insert(i,p)
        self.last_valid_time = p.v


    def find_point(self,v):
        for each in self.points:
            if each.v == float(v):
                return each
        return None




    def add_edge(self,edge,start_time,end_time):
        if start_time == None and end_time == None:
            start_time = self.last_valid_time + 0.1
            end_time = start_time + 0.1
        start = self.find_point(start_time)
        if (start == None):
            start = TimePoint(start_time)
            self.insert_point(start)
        end = self.find_point(end_time)
        if (end == None):
            end = TimePoint(end_time)
            self.insert_point(end)

        edge.set_start_time_point(start)
        edge.set_end_time_point(end)

        start.add_outgoing(edge)
        end.add_incoming(edge)

    def get_last_node(self):
        return self.points[-1]


class DialogTimelineBuilder():

    def __init__(self,dialog):
        self.dialog = dialog
        self.timeline = DialogTimeline()

    # return the time line after it was build
    def get_timeline(self):
        return self.timeline

    def build(self):
        #iterte of the terminal and build them
        for x in self.dialog.terminals:
            self.add_terminal(x)
        # no need to add the parse trees
        #for x in self.dialog.parses:
        #    self.add_parse(x)
        for x in self.dialog.turns:
            self.add_turn(x)
        for x in self.dialog.dialacts:
            self.add_dialact(x)

        #todo: the same for all the other relations.

    def add_terminal(self,t):
        self.timeline.add_edge(t,t.get_start_time(),t.get_end_time())

    def add_parse(self,parse):
        print "add parse %s" % parse
        self.timeline.add_edge(parse,parse.get_start_time(),parse.get_end_time())

    def add_turn(self,turn):
        print "add turn %s" % turn
        self.timeline.add_edge(turn,turn.get_start_time(),turn.get_end_time())

    def add_nt(self,nt):
        print "add nt %s" % nt
        self.timeline.add_edge(nt,nt.get_start_time(),nt.get_end_time())

    def add_dialact(self,dialact):
        print "add dialact %s" % dialact
        self.timeline.add_edge(dialact,dialact.get_start_time(),dialact.get_end_time())

CSV_DIR = "C:\\temp\\dialogs_csv\\"

class GraphBuilder():
    def __init__(self):
        self.graph = Neo4JGraph("neo4j", "Israel1971")
        self.graph.connect()
        self.topics_nodes = {} # map from topic id topics
        self.speaker_nodes = {} # map from speaker id to speaker

    def make_csv_dir(self):
        if not os.path.exists(CSV_DIR):
            os.makedirs(CSV_DIR)

    def dump(self,dialog_node):
          path =  CSV_DIR + dialog_node.id
          df = pd.DataFrame(query.all_dacts_q())
          df.to_csv(path)

    def mergecsv(self):
        # read all the files in the csv directory
        dfs = []
        for i in os.listdir("C:\\temp\\dialogs_csv\\"):
            df = pd.read_csv("C:\\temp\\dialogs_csv\\"+i)
            dfs.append(df)
        all_df = pd.concat(dfs)
        all_df.to_csv(CSV_DIR + "all_df.csv")      

    def clean(self):
        self.graph.clean()        

    def add_nt(self, nt):
        start_time_node = self.make_time_node(nt.get_start_time(),nt.dialog)
        self.graph.get_graph().create(start_time_node)

        end_time_node = self.make_time_node(nt.get_end_time(),nt.dialog)
        self.graph.get_graph().create(end_time_node)

        nt_relation = Relationship(start_time_node,
                                   "NT",
                                   end_time_node,
                                   id=nt.id,
                                   href=nt.href,
                                   start=nt.start,
                                   end=nt.end,
                                   wc=nt.wc,
                                   cat=nt.cat)

        self.graph.get_graph().create(nt_relation)

        for x in nt.nt_list():
            self.add_nt(x)


    def add_topics(self,corpus1):
        for k, v in corpus1.topic_nodes.iteritems():
            print "creating topics %s" % k
            # register
            topic = Node("Topic", abstract=v.abstract, question=v.question, id=v.id, href=v.href)
            self.graph.get_graph().create(topic)
            self.topics_nodes[v.href] = topic


    def add_speakers(self,corpus1):
        for k, v in corpus1.speaker_nodes.iteritems():
            print "creating speaker %s" % k
            # register
            speaker = Node("Speaker", id=v.id, href=v.href, dob=v.dob)
            self.graph.get_graph().create(speaker)
            self.speaker_nodes[v.href] = speaker


    def add_edge(self,start_node,edge,end_node):
         #if an edge is of type terminalk
         e = None # the edge
         if isinstance(edge, WordRelation):
            e = self.make_word_relation(edge,start_node,end_node)
         if isinstance(edge, PuncRelation):
            e = self.make_punc_relation(edge,start_node,end_node)
         if isinstance(edge, SilRelation):
            e = self.make_sil_relation(edge,start_node,end_node)
         if isinstance(edge, TraceRelation):
            e = self.make_trace_relation(edge,start_node,end_node)
         # if and edge is of type parse
         if isinstance(edge, ParseRelation):
            e = self.make_parse_relation(edge,start_node,end_node)
         # if and edge is of type nt
         if isinstance(edge, NonTerminalRelation):
            e = self.make_nt_relation(edge,start_node,end_node)
         # if and edge is of type turn
         if isinstance(edge, TurnRelation):
            e = self.make_turn_relation(edge,start_node,end_node)
         if isinstance(edge, OpenFloorRelation):
            e = self.make_openfloor_relation(edge,start_node,end_node)
         if isinstance(edge, DialogActRelation):
             e = self.make_dialact_relation(edge,start_node,end_node)
         self.graph.get_graph().create(e)

    def add_metadata(self,corpus1):
        self.add_topics(corpus1)
        self.add_speakers(corpus1)
        for k, v in corpus1.dialog_nodes.iteritems():
                # register
                dialogue = Node("Dialogue", id=v.id, swbid=v.swbdid, href=v.href)
                self.graph.get_graph().create(dialogue)
                logger.debug("full load, addding speaker")

                speaker_A = self.speaker_nodes[v.A_id]
                speaker_B = self.speaker_nodes[v.B_id]
                topic = self.topics_nodes[v.topic_id]

                rel = Relationship(dialogue, "A", speaker_A)
                self.graph.get_graph().create(rel)
                rel = Relationship(dialogue, "B", speaker_B)
                self.graph.get_graph().create(rel)
                rel = Relationship(dialogue, "TOPIC", topic)
                self.graph.get_graph().create(rel)
                break
 
    def add_dialog_timeline(self,dialog_node):
                logger.debug("creating dialog %s" % len(dialog_node.timeline.points))

                for p in dialog_node.timeline.points:
                    node = self.make_time_point_node(p,dialog_node.id)
                    self.graph.get_graph().create(node)
                    p.set_graph_node(node)

                logger.debug("done creating time points")


                # create the edges in the graph
                for p in dialog_node.timeline.points:
                    for o in p.outgoing_nodes:
                        e = o.end_time_point
                        start_node = p.get_graph_node()
                        end_node = e.get_graph_node()
                        self.add_edge(start_node,o,end_node)
                        logger.debug("added %s " % str(o))

    def build(self, corpus,full_load=False):
        logger.info("build")
        
        self.add_topics(corpus)
        self.add_speakers(corpus)
        for k, v in corpus.dialog_nodes.iteritems():
            if len(v.terminals) > 0:
                # register
                dialogue = Node("Dialogue", id=v.id, swbid=v.swbdid, href=v.href)
                self.graph.get_graph().create(dialogue)

                # todo: open when we do the full load
                if full_load:
                    logger.debug("full load, addding speaker")

                    speaker_A = self.speaker_nodes[v.A_id]
                    speaker_B = self.speaker_nodes[v.B_id]
                    topic = self.topics_nodes[v.topic_id]

                    rel = Relationship(dialogue, "A", speaker_A)
                    self.graph.get_graph().create(rel)
                    rel = Relationship(dialogue, "B", speaker_B)
                    self.graph.get_graph().create(rel)
                    rel = Relationship(dialogue, "TOPIC", topic)
                    self.graph.get_graph().create(rel)

                time_line = v.timeline
                # create the nodes in graph
        
   
    def make_word_relation(self,t,start_time_node,end_time_node):
            return  Relationship(start_time_node,
                                 "WORD",
                                 end_time_node,
                                 dialog     = t.dialog_id,
                                 speaker    = t.speaker_id,
                                 start      = t.get_start_time(),
                                 end        = t.get_end_time(),
                                 id         = t.id,
                                 href       = t.href,
                                 pos        = t.pos,
                                 orth       = t.orth,
                                 phon_href  = t.phon_id)

    def make_punc_relation(self,t,start_time_node,end_time_node):
            return  Relationship(start_time_node, "PUNC", end_time_node,
                                             id=t.id,
                                             dialog     = t.dialog_id,
                                             speaker    = t.speaker_id,
                                             start      = t.get_start_time(),
                                             end        = t.get_end_time(),
                                             href=t.href,
                                             txt=t.txt)

    def make_sil_relation(self,t,start_time_node,end_time_node):
            return  Relationship(start_time_node, "SIL", end_time_node,
                                             id=t.id,
                                             dialog     = t.dialog_id,
                                             speaker    = t.speaker_id,
                                             start      = t.get_start_time(),
                                             end        = t.get_end_time(),
                                             href=t.href)

    def make_trace_relation(self,t,start_time_node,end_time_node):
            return  Relationship(start_time_node, "TRACE", end_time_node,
                                             dialog     = t.dialog_id,
                                             speaker    = t.speaker_id,
                                             start      = t.get_start_time(),
                                             end        = t.get_end_time(),
                                             id=t.id,
                                             href=t.href)

    def make_parse_relation(self,t,start_time_node,end_time_node):
            return Relationship(start_time_node,
                                "PARSE",
                                end_time_node,
                                dialog     = t.dialog_id,
                                speaker    = t.speaker_id,
                                start      = t.get_start_time(),
                                end        = t.get_end_time(),
                                id         = t.id,
                                href       = t.href)

    def make_turn_relation(self,t,start_time_node,end_time_node):
            return Relationship(start_time_node,
                                "TURN",
                                end_time_node,
                                id          =  t.id,
                                dialog      =  t.dialog_id,
                                speaker     =  t.speaker_id,
                                start       =  t.get_start_time(),
                                end         =  t.get_end_time(),
                                href        =  t.href,
                                turn_change =  t.turn_change)


    def make_openfloor_relation(self,t,start_time_node,end_time_node):
            return Relationship(start_time_node,
                "OPEN_FLOOR",
                end_time_node,
                start=t.start,
                end=t.end)

    def make_nt_relation(self,nt,start_time_node,end_time_node):
            return Relationship(start_time_node,
                                   "NT",
                                   end_time_node,
                                   id          =  nt.id,
                                   dialog      =  nt.dialog_id,
                                   speaker     =  nt.speaker_id,
                                   start       =  nt.get_start_time(),
                                   end         =  nt.get_end_time(),
                                   href=nt.href,
                                   wc=nt.wc,
                                   cat=nt.cat)


    def make_dialact_relation(self,t,start_time_node,end_time_node):
             return Relationship(start_time_node,
                                "DIALACT",
                                end_time_node,
                                id          =  t.id,
                                dialog      =  t.dialog_id,
                                speaker     =  t.speaker_id,
                                start       =  t.get_start_time(),
                                end         =  t.get_end_time(),
                                href        =  t.href,
                                swbdType    =  t.swbdType,
                                niteType    =  t.niteType)

    def make_time_point_node(self, p,d):
        return Node("TIMEPOINT", time=p.v,dialog = d)

 

if __name__ == '__main__':
    logger.info("main: starting")
    #create_graph()