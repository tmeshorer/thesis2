__author__ = 'Tomer'

import os
import json
import logging

from corpus_resources import *
from datastructure import Neo4JGraph

from py2neo.packages.httpstream import http
http.socket_timeout = 9999

#==============================================================================
#========================= Queries on turns ===================================
#==============================================================================

logger = logging.getLogger('curpus')

# return all the turns in the database
def all_turns() :
    return "MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT) RETURN turn"

def turn_secs():
    """
    Set the turn length in seconds
    """

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn, (turn_end.time - turn_start.time) AS length
        SET turn.secs = length
        return turn
        """

def turn_words():
    """
    Set the turn length in words
    """
    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (word_start:TIMEPOINT)-[word:WORD]->(word_end:TIMEPOINT)
        WHERE word_start.time>=turn_start.time AND word_end.time<=turn_end.time
        WITH turn,COUNT(*) AS word_count
        SET turn.words = word_count
        RETURN turn
    """


def turn_avg_secs():
    """
    Compute the avg turn length in seconds
    """
    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn_start.time AS st, turn.speaker AS speaker, turn
        MATCH(turn_start_2:TIMEPOINT)-[turn2:TURN]->(turn_end_2:TIMEPOINT)
        WHERE turn_end_2.time < st AND turn2.speaker = speaker
        WITH turn, AVG(turn2.secs) AS prev_avg_length
        SET turn.avg_secs = prev_avg_length
        RETURN turn
    """

def turn_avg_words():
    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn_start.time AS st, turn.speaker AS speaker, turn
        MATCH(turn_start_2:TIMEPOINT)-[turn2:TURN]->(turn_end_2:TIMEPOINT)
        WHERE turn_end_2.time < st AND turn2.speaker = speaker
        WITH turn, AVG(turn2.words)  AS prev_avg_words_count
        SET turn.avg_words = prev_avg_words_count
        RETURN turn
    """

def turn_total_speaker_secs():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn_start.time AS st, turn.speaker AS speaker, turn
        MATCH(turn_start_2:TIMEPOINT)-[turn2:TURN]->(turn_end_2:TIMEPOINT)
        WHERE turn_end_2.time < st AND turn2.speaker = speaker
        WITH  turn,SUM(turn2.secs) AS time_sum_for_speaker
        SET turn.total_speaker_secs = time_sum_for_speaker
        RETURN turn
    """

def turn_total_secs():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn_start.time AS st, turn
        MATCH(turn_start_2:TIMEPOINT)-[turn2:TURN]->(turn_end_2:TIMEPOINT)
        WHERE turn_end_2.time < st
        WITH  turn,SUM(turn2.secs) AS total_time_sum
        SET turn.total_secs = total_time_sum
        RETURN turn
    """

def turn_time_control() :

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WHERE turn.total_secs > 0
        SET turn.time_control = turn.total_speaker_secs * 100/ turn.total_secs
        RETURN turn
    """

def turn_speaker_words():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn_start.time AS st, turn.speaker AS speaker, turn
        MATCH(turn_start_2:TIMEPOINT)-[turn2:TURN]->(turn_end_2:TIMEPOINT)
        WHERE turn_end_2.time < st AND turn2.speaker = speaker
        WITH  turn,SUM(turn2.words) AS word_sum_for_speaker
        SET turn.speaker_words = word_sum_for_speaker
        RETURN turn
    """

def turn_all_words():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH turn_start.time AS st, turn
        MATCH(turn_start_2:TIMEPOINT)-[turn2:TURN]->(turn_end_2:TIMEPOINT)
        WHERE turn_end_2.time < st
        WITH  turn,SUM(turn2.words) AS total_word_sum
        SET turn.all_words = total_word_sum
        RETURN turn
    """

def turn_words_control():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WHERE turn.all_words > 0
        SET turn.words_control = turn.speaker_words*100 / turn.all_words
        RETURN turn
    """


def clean_turns():
    return """
        MATCH ()-[turn:TURN]->()
        DELETE turn
    """


#==============================================================================
#========================= Queries on dialog acts =============================
#==============================================================================


def all_dacts() :
    return "MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT) RETURN da"

def all_dacts_q():
    return execute(all_dacts())

#Dialog act length
#===================
def da_words():

    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        MATCH (word_start:TIMEPOINT)-[word:WORD]->(word_end:TIMEPOINT)
        WITH word_start,word_end,da_start,da_end,da
        WHERE word_start.time>=da_start.time AND word_end.time<=da_end.time  
        WITH da,COUNT(*) AS word_count
        SET da.words = word_count
        RETURN da
    """

def da_secs():

    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da, (da_end.time - da_start.time) AS length
        SET da.secs = length
        return da
        ORDER BY da.start
        """


#Turn time length
#===================



def dact_avg_turn_secs():
    """
    Assign the avg turns to each dialog act
    """
    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.tid = turn.id
        SET dact.avg_turn_secs = turn.avg_secs
        RETURN dact
    """


def da_time_sofar():
    """
    compute the time so far
    """
    return """
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        SET dact.time_sofar = dact.end - dact.tstart
        RETURN dact
        ORDER BY dact.start
    """


      
def da_precent_secs_sofar():
    """
    compute the time so far in the da as a precentage of the avg turn length
    """

    return """
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.avg_turn_secs > 0
        SET dact.precent_secs_sofar = dact.time_sofar*100/dact.avg_turn_secs
        return dact
    """



def da_avg_turn_words():
     return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.tid = turn.id
        SET dact.avg_turn_words = turn.avg_words
        RETURN dact
    """

def init_da_words_sofar():
    return """    
    MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
    WITH dact
    SET dact.words_sofar = dact.words
    RETURN dact
    """

def da_words_sofar():
    from neo4jrestclient.client import GraphDatabase
    gdb = GraphDatabase("http://localhost:7474/db/data/", username="neo4j", password="Israel1971")
    ids = dict()
    q = "MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT) RETURN turn"
    turns = gdb.query(q=q)
    for each_turn in turns:
        start = each_turn[0]["data"]["start"]
        end = each_turn[0]["data"]["end"]
        q_dacts = "MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT) WHERE %f<=dact_start.time AND %f>=dact_end.time return dact" % (
        start, end)
        dacts = gdb.query(q=q_dacts)
        total_words = 0
        for da in dacts:
            words = da[0]['data']['words']
            da_id = da[0]['data']['id']
            total_words += words
            ids[da_id] = total_words

    for k, v in sorted(ids.items()):
        if v != None:
            q = "MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT) WHERE dact.id = '%s' SET dact.words_sofar=%s RETURN dact" % (
            k, v)
            print k
            print v
            dacts = gdb.query(q=q)

def precent_words_sofar(): 

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.tid = turn.id
        WITH  dact
        SET dact.precent_words_sofar = dact.words_sofar*100/dact.avg_turn_words 
        return dact
    """


def dact_time_control():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.tid = turn.id
        WITH  dact,turn
        SET dact.time_control = turn.time_control 
        RETURN dact
    """


def dact_turn_id():
    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE turn_start.time<=dact_start.time AND turn_end.time>=dact_end.time
        WITH  dact,turn
        SET dact.tid = turn.id,
            dact.tstart = turn.start,
            dact.tend   = turn.end
        RETURN dact
    """

def dact_turn_attrs():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.tid = turn.id
        WITH  dact,turn
        SET dact.tspeaker_words = turn.speaker_words,
            dact.tall_words     = turn.all_words,
            dact.ttotal_speaker_secs = turn.total_speaker_secs,
            dact.total_secs          = turn.total_secs
        RETURN dact
    """


def dact_words_control():

    return """
        MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
        WITH   turn_start,turn_end,turn
        MATCH (dact_start:TIMEPOINT)-[dact:DIALACT]->(dact_end:TIMEPOINT)
        WHERE dact.tid = turn.id
        WITH  dact,turn
        SET dact.words_control = turn.words_control 
        RETURN dact
    """
 

def da_prev_da():

    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da_start.time AS st, da.speaker AS speaker, da
        MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
        WHERE da_end_2.time < st 
        WITH COLLECT(da2.swbdType) AS prev_da,da
        SET da.p_da = last(prev_da)
        RETURN da
        ORDER BY da.start
    """


def da_prev_speaker():

    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da_start.time AS st, da.speaker AS speaker, da
        MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
        WHERE da_end_2.time < st 
        WITH COLLECT(da2.speaker) AS prev_speaker,da
        SET da.p_speaker = last(prev_speaker)
        RETURN da
        ORDER BY da.start
    """


def clean_all():
    execute(clean_parse())
    execute(clean_nt())
    execute(clean_turns())
    execute(clean_dacts())
    execute(clean_words())
    execute(clean_sil())
    execute(clean_punc())
    execute(clean_trace())
    execute(clean_open_floor())
    execute(clean_timepoints())

def print_count(rel_type,q):
    result = execute(q)
    logger.info("there are %s : %s" %(rel_type,str(len(result))))

def print_all():
    print_count("dact",count_dialog_acts())
    print_count("words",count_words())
    print_count("turns",count_turns())
    print_count("parse",count_parse())
    print_count("trace",count_trace())
    print_count("sil",count_sil())
    print_count("nt",count_nt())


def create_index_on_time():
    g = Neo4JGraph("neo4j", PASSWORD)
    g.connect()
    g.get_graph().run("CREATE INDEX ON :TIMEPOINT(time)")

def count_trace():
    return """
        MATCH ()-[da:TRACE]->()
        RETURN da
    """

def count_sil():
    return """
        MATCH ()-[da:SIL]->()
        RETURN da
    """

def count_nt():
    return """
        MATCH ()-[nt:NT]->()
        RETURN nt
    """



def count_dialog_acts():
    return """
        MATCH ()-[da:DIALACT]->()
        RETURN da
    """

def count_words():
    return """
        MATCH ()-[w:WORD]->()
        RETURN w
    """

def count_sil():
    return """
        MATCH ()-[s:SIL]->()
        RETURN s
    """

def count_trace():
    return """
        MATCH ()-[s:TRACE]->()
        RETURN s
    """

def count_turns():
    return """
        MATCH ()-[s:TURN]->()
        RETURN s
    """

def count_parse():
    return """
        MATCH ()-[s:PARSE]->()
        RETURN s
    """


def clean_dacts():
    return """
        MATCH ()-[da:DIALACT]->()
        DELETE da
    """
     
def clean_words():
    return """
        MATCH ()-[w:WORD]->()
        DELETE w
    """

def clean_sil():
    return """
        MATCH ()-[s:SIL]->()
        DELETE s
    """

def clean_timepoints():
    return """
        MATCH (t:TIMEPOINT)-[]->()
        DELETE t
    """

def clean_parse():
    return """
        MATCH ()-[t:PARSE]->()
        DELETE t
    """

def clean_nt():
    return """
        MATCH ()-[t:NT]->()
        DELETE t
    """

def clean_punc():
    return """
        MATCH ()-[t:PUNC]->()
        DELETE t
    """

def clean_turn():
    return """
        MATCH ()-[t:TURN]->()
        DELETE t
    """

def clean_open_floor():
    return """
        MATCH ()-[t:OPEN_FLOOR]->()
        DELETE t
    """

def clean_trace():
    return """
        MATCH ()-[t:TRACE]->()
        DELETE t
    """

PASSWORD="Israel1971"




def run_q():
    print "create index on time"
    create_index_on_time()
    print "turn_secs"
    execute(turn_secs())
    print "turn words"
    execute(turn_words())
    print "turn avg secs"
    execute(turn_avg_secs())
    print "turn avg words"
    execute( turn_avg_words())
    print "turn total secs"
    execute( turn_total_secs())
    print "turn speaker words"
    execute(turn_speaker_words())
    print "turn all words"
    execute(turn_all_words())
    print "turn total speaker secs"
    execute( turn_total_speaker_secs())
    print "turn time control"
    execute( turn_time_control() )
    print "turn words control"
    execute( turn_words_control())

    #==== dact ===================
    print "dact turn attrs"
    execute( dact_turn_attrs())
    print "create index on dact turn id"
    execute( dact_turn_id() )
    print "da words"
    execute( da_words())
    print "da secs"
    execute( da_secs())
    print "dact avg turn secs"
    execute( dact_avg_turn_secs())
    print "da time sofar"
    execute( da_time_sofar())
    print "da precent so far"
    execute( da_precent_secs_sofar())
    print "da avg turn words"
    execute( da_avg_turn_words())
    print "init da words sofar"
    execute( init_da_words_sofar())
    print "da words so far"
    da_words_sofar() # we do manual analysis
    print "precent words so far"
    execute( precent_words_sofar())
    print "dact time control"
    execute( dact_time_control())
    print "dact words control"
    execute( dact_words_control())
    print "da prev da"
    execute( da_prev_da())
    print "da prev speaker"
    execute( da_prev_speaker())

def clear_data():
    g = Neo4JGraph("neo4j", PASSWORD)
    g.connect()
    g.clean()

def execute(q):
    g = Neo4JGraph("neo4j", PASSWORD)
    g.connect()
    print "executing %s" % q
    record_list = g.get_graph().data(q)
    return record_list

def to_csv(fname):
    import pandas as pd
    from neo4jrestclient.client import GraphDatabase
    gdb = GraphDatabase("http://localhost:7474/db/data/", username="neo4j", password="Israel1971")

    q = "MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT) RETURN da"
    dialogs = gdb.query(q=q)
    result = []
    for da in dialogs:
        result.append(da[0]["data"])
    df = pd.DataFrame(result)
    df.to_csv(fname)
    
if __name__ == '__main__':
    da_words_sofar()