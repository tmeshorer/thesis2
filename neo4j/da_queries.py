__author__ = 'Tomer'

import os
import json
import logging
from py2neo import Graph, Node, Relationship, authenticate
from datastructure import Graph
from corpus_resources import CorpusResourcesDir
from terminal import TerminalDir, WordRelation, adj_start_and_time, PuncRelation, SilRelation, TraceRelation
from syntax import SyntaxDir, ParseRelation, NonTerminalRelation
from turn import TurnDir, TurnRelation, OpenFloorRelation
from dialact import DialogActDir, DialogActRelation
from datastructure import Neo4JGraph


def dialog_act_length_in_words():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
                WITH   da_start,da_end,da
                MATCH (word_start:TIMEPOINT)-[word:WORD]->(word_end:TIMEPOINT)
                WHERE word_start.time>=da_start.time AND word_end.time<=da_end.time
                WITH da,COUNT(*) AS word_count
                SET da.length_in_words = word_count"""


def dialog_act_length_in_word():
    return """
     MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
            WITH da, (da_end.time - da_start.time) AS length
            SET da.length_in_time = length
     """


def mean_length_in_time():
    return """
         MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
         WITH da_start.time AS st, da.speaker AS speaker, da
         MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
         WHERE da_end_2.time < st AND da2.speaker = speaker
         WITH
         da,
         AVG(da2.length_in_time)     AS mean_length_in_time
         SET da.mean_length_in_time  = mean_length_in_time"""

def zero_pause_count():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da
        SET da.pause_count=0"""



def mean_length_in_word():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
              WITH da_start.time AS st, da.speaker AS speaker, da
              MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
              WHERE da_end_2.time < st AND da2.speaker = speaker
              WITH
              da,
              AVG(da2.length_in_words)      AS mean_length_in_words
              SET da.mean_length_in_words      = mean_length_in_words"""


def da_so_far_by_speaker():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da_start.time AS st, da.speaker AS speaker, da
        MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
        WHERE da_end_2.time < st AND da2.speaker = speaker
        WITH  da,Count(*) AS prev_da_count
        SET da.da_so_far_by_speaker = prev_da_count"""



def da_so_far_by_all():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
                WITH da_start.time AS st, da.speaker AS speaker, da
                MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
                WHERE da_end_2.time < st
                WITH  da,Count(*) AS prev_da_count
                SET da.total_da_count_by_all = prev_da_count"""


def sil_length_in_time():
    return """MATCH (sil_start:TIMEPOINT)-[sil:SIL]->(sil_end:TIMEPOINT)
          WITH sil, (sil_end.time - sil_start.time) AS length
          SET sil.length_in_time = length"""


def mean_pause_time():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
         WITH   da_start,da_end,da
         MATCH (sil_start:TIMEPOINT)-[sil:SIL]->(sil_end:TIMEPOINT)
         WHERE sil_start.time>=da_start.time AND sil_end.time<=da_end.time
         WITH da,AVG(sil.length_in_time) AS sil_avg
         SET  da.mean_pause_time = sil_avg"""



def pause_count():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH   da_start,da_end,da
        MATCH (sil_start:TIMEPOINT)-[sil:SIL]->(sil_end:TIMEPOINT)
        WHERE sil_start.time>=da_start.time AND sil_end.time<=da_end.time
        WITH da,COUNT(*) AS sil_count
        SET da.pause_count   =  sil_count
        RETURN da
        ORDER BY da.start"""


def mean_pause_count():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
          WITH da_start.time AS st, da.speaker AS speaker, da
          MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
          WHERE da_end_2.time < st AND da2.speaker = speaker
          WITH
          da,
          AVG(da2.pause_count)     AS mean_pause_count
          SET da.mean_pause_count  = mean_pause_count"""


def prev_da():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
          WITH da_start.time AS st, da.speaker AS speaker, da
          MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
          WHERE da_end_2.time < st
          WITH COLLECT(da2.swbdType) AS prev_da,da
          SET da.prev_da = last(prev_da)"""


def prev_speaker():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
          WITH da_start.time AS st, da.speaker AS speaker, da
          MATCH(da_start_2:TIMEPOINT)-[da2:DIALACT]->(da_end_2:TIMEPOINT)
          WHERE da_end_2.time < st
          WITH COLLECT(da2.speaker) AS prev_speaker,da
          SET da.prev_speaker = last(prev_speaker)"""


# ----------------------------- Length in words ----------------

def precent_of_words():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da
        SET da.precent_length_in_words = da.length_in_words*100/da.mean_length_in_words"""


def precent_legnth_in_time():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da
        SET da.precent_length_in_time = da.length_in_time*100/da.mean_length_in_time"""


def precent_turn_count():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da
        SET da.precent_da_count = da.da_so_far_by_speaker*100/da.total_da_count_by_all"""


def precent_pause_time():
    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da
        WHERE da.mean_mean_pause_time > 0
        SET da.precent_mean_pause_time = da.mean_pause_time*100/da.mean_mean_pause_time"""


def precenet_mean_count():
    return """
         MATCH (turn_start:TIMEPOINT)-[turn:TURN]->(turn_end:TIMEPOINT)
          WITH turn
                WHERE turn.mean_pause_count > 0
                SET turn.precent_mean_pause_count = turn.pause_count*100/turn.mean_pause_count"""


def question_count():
    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da_start.time AS st, da.speaker AS speaker, da
        MATCH (da2_start:TIMEPOINT)-[da2:DIALACT]->(da2_end:TIMEPOINT)
        WHERE da2_end.time<=st
        AND da2.swbdType = 'qh'
        AND da2.speaker = speaker
        WITH da,count(da2) AS q_dact_count
        SET da.question_count = q_dact_count"""


def question_precent():
    return """
        MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da
        SET da.precent_q = da.q_count*100/da.da_so_far_by_speaker"""


def back_channel_count():
    return """MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
        WITH da_start.time AS st, da.speaker AS speaker, da
        MATCH (da2_start:TIMEPOINT)-[da2:DIALACT]->(da2_end:TIMEPOINT)
        WHERE da2_end.time<=st
        AND da2.swbdType = 'b'
        AND da2.speaker = speaker
        WITH da,count(da2) AS q_dact_count
        SET da.backchannel_count = q_dact_count"""


def backchannel_precent():
    return"""
    MATCH (da_start:TIMEPOINT)-[da:DIALACT]->(da_end:TIMEPOINT)
    WITH da
    SET da.precent_bc = da.backchannel_count*100/da.da_so_far_by_speaker"""


def run_q():
    execute(zero_pause_count())
    execute(dialog_act_length_in_words())
    execute(dialog_act_length_in_word())
    execute(mean_length_in_time())
    execute(mean_length_in_word())
    execute(da_so_far_by_speaker())
    execute(da_so_far_by_all())
    execute(sil_length_in_time())
    execute(mean_pause_time())
    execute(pause_count())
    execute(mean_pause_count())
    execute(prev_da())
    execute(prev_speaker())
    execute(precent_of_words())
    execute(precent_legnth_in_time())
    execute(precent_turn_count())
    execute(precent_pause_time())
    execute(precenet_mean_count())
    execute(question_count())
    execute(question_precent())
    execute(back_channel_count())
    execute(backchannel_precent())


def execute(q):
    g = Neo4JGraph("neo4j", "sagito")
    g.connect()
    record_list = g.get_graph().cypher.execute(q)
    for record in record_list:
        turn = record[0]
        #     turn.properties["name"] = "tomer"
        #     turn.push()
        print turn.properties


if __name__ == '__main__':
    run_q()
