__author__ = 'Tomer'

import xmltodict
import os
from pandas import DataFrame
from py2neo import Node, Relationship
import logging
logger = logging.getLogger('curpus')


def create_href(fname,nite_id):
    return fname + "#id(" + nite_id + ")"

#<word pos="UH" nite:id="s1_1" msstateID="sw2005A-ms98-a-0001-2" msstate="sw2005A-ms98-a-0001" nite:end="1.280000" nite:start="0.800000" orth="Okay">
#	<nite:pointer role="phon" href="sw2005.A.phonwords.xml#id(ms1A_pw1)"/>
#</word>

class TerminalDir():
    def __init__(self,path):
        self.path = path
        self.dialogs = {}
        self.all_terminals = []

    def read(self,dialog_node):
        logger.info("enter terminal dir for %s " % dialog_node.id)
        for i in os.listdir(self.path):
            parts = i.split('.')
            dialog_id = parts[0]
            speaker_id= parts[1]
            if dialog_node.get_sw_id() == dialog_id:
                f = TerminalFile(self.path+"\\"+i,i,dialog_id,speaker_id)
                terminal_list = f.read()
                logger.info("read terminals files %s, read %s " % (dialog_id,len(terminal_list)))

                for t in terminal_list:
                    self.all_terminals.append(t)

                if not dialog_id in self.dialogs:
                    self.dialogs[dialog_id] = {}
                speakers_in_dialogs = self.dialogs[dialog_id]
                speakers_in_dialogs[speaker_id] = terminal_list
           
    def as_data_frame(self):
        return DataFrame(self.all_terminals)




class TerminalFile():
    def __init__(self,path,fname,dialog_id,spaker_id):
        self.path = path
        self.fname = fname
        self.dialog_id  = dialog_id
        self.speaker_id = spaker_id

        logger.info("TerminalFile::init() %s %s" % (self.path,self.fname))


    def read(self):
        logger.info("enter TerminalFile::read() %s %s" % (self.speaker_id,self.dialog_id))
        result = []
        with open(self.path) as fd:
              obj = xmltodict.parse(fd.read())
              for x in obj["nite:terminal_stream"]["word"]:
                   w = WordRelation(self.dialog_id,self.speaker_id,self.fname)
                   w.read(x)
                   result.append(w)
              for x in obj["nite:terminal_stream"]["punc"]:
                   w = PuncRelation(self.dialog_id,self.speaker_id,self.fname)
                   w.read(x)
                   result.append(w)
              for x in obj["nite:terminal_stream"]["sil"]:
                   w = SilRelation(self.dialog_id,self.speaker_id,self.fname)
                   w.read(x)
                   result.append(w)
              for x in obj["nite:terminal_stream"]["trace"]:
                   t = TraceRelation(self.dialog_id,self.speaker_id,self.fname)
                   t.read(x)
                   result.append(t)


              # sort the terms by id
        return result




class WordRelation():
    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id = dialog_id
        self.speaker_id = speaker_id
        self.id =   None
        self.orth = None
        self.pos  = None #part of speech
        self.start = None
        self.end = None
        self.phon_id = None
        self.phon = None
        self.fname = fname
        self.start_time_point = None
        self.end_time_poinr = None
        self.overlapp_speech = False # indicate if this is an overlap speech

    def as_dict(self):
        result = {}
        result['type']          = "word"
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['id'] = self.id
        result['orth'] = self.orth
        result['pos']  = self.pos
        result['start'] = self.get_start_time()
        result['end']   = self.get_end_time()
        result['phon_id'] = self.phon_id
        result['phon'] = self.phon
        result['fname'] = self.fname
        return result



    def read(self,m):
         self.id    = m['@nite:id']
         self.pos   = m['@pos']
         start_value = m['@nite:start']
         if start_value != "non-aligned" and start_value!="n/a":
            self.start = float(start_value)
         end_value = m['@nite:end']
         if end_value != "non-aligned" and end_value != "n/a":
            self.end = float(end_value)

         # if we have a start time with no end time, set the end time to start time + 0.5 milsec
         if (self.start != None and self.end == None):
             self.end = self.start + 0.05

         if (self.start == None and self.end != None):
             self.start = self.end - 0.05

         self.orth  = m["@orth"]
         self.phon_id = "none"
         if "nite:pointer" in m:
              self.phon_id = m["nite:pointer"]["@href"]
         self.href = create_href(self.fname,self.id)

    def get_start_time(self):
        return self.start

    def get_end_time(self):
        return self.end

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p

    def __str__(self):
        return "Word(%s, %s %s, %s , from %s to %s)" % (self.dialog_id,self.speaker_id,self.id,self.orth,self.start, self.end)


#<punc nite:id="s1_2">.</punc>
class PuncRelation() :
    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id = dialog_id
        self.speaker_id = speaker_id
        self.id  = None
        self.txt = None
        self.href = None
        self.fname = fname
        self.start = None
        self.end   = None
        self.start_time_point = None
        self.end_time_point = None

    def read(self,m):
        self.id  = m['@nite:id']
        if "#text" in m:
            self.txt = m["#text"]
        else:
            raise Exception(self.__str__() + " does no have a text")

        self.href = create_href(self.fname,self.id)

    def as_dict(self):
        result = {}
        result['type'] = "punc"
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['txt'] = self.txt
        result['href'] = self.href
        result['start'] = self.get_start_time()
        result['end']   = self.get_end_time()
        result['fname'] = self.fname
        return result


    def __str__(self):
        return "Punc(%s %s %s, %s - %s)" % (self.dialog_id,self.speaker_id,self.id,self.start,self.end)

    def get_start_time(self):
        return self.start

    def get_end_time(self):
        return self.end

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p



class SilRelation() :
    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id =dialog_id
        self.speaker_id =speaker_id
        self.fname = fname
        self.start = None
        self.end   = None
        self.start_time_point = None
        self.end_time_point = None


    def as_dict(self):
        result = {}
        result['type'] = "sil"
        result['dialog_id']  = self.dialog_id
        result['speaker_id'] = self.speaker_id
        result['txt'] = self.txt
        result['href'] = self.href
        result['start'] = self.get_start_time()
        result['end']   = self.get_end_time()
        result['fname'] = self.fname
        return result

    def read(self,m):
        self.id  = m['@nite:id']
        self.href = create_href(self.fname,self.id)

    def __str__(self):
        return "Sil(%s %s %s, %s - %s)" % (self.dialog_id,self.speaker_id,self.id,self.start,self.end)

    def get_start_time(self):
        return self.start

    def get_end_time(self):
        return self.end

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p

class TraceRelation() :
    def __init__(self,dialog_id,speaker_id,fname):
        self.dialog_id =dialog_id
        self.speaker_id =speaker_id
        self.fname = fname
        self.start = None
        self.end   = None
        self.start_time_point = None
        self.end_time_point = None

    def read(self,m):
        self.id  = m['@nite:id']
        self.href = create_href(self.fname,self.id)

    def __str__(self):
        return "Sil(%s %s %s, %s - %s)" % (self.dialog_id,self.speaker_id,self.id,self.start,self.end)

    def get_start_time(self):
        return self.start

    def get_end_time(self):
        return self.end

    def set_start_time_point(self,p):
        self.start_time_point = p

    def set_end_time_point(self,p):
        self.end_time_point = p




def adj_start_and_time(tlist):
    last_end_time   = 0
    for i in range(0,len(tlist)-1):
        t = tlist[i]
        if isinstance(t,WordRelation):
            if t.get_start_time() != None:
                #check for overlapp speech
                if t.get_start_time() < last_end_time:
                    t.overlapp_speech = True
                    if t.get_end_time() > last_end_time:
                        last_end_time = t.get_end_time()
                    continue
                if t.get_end_time() != None:
                    last_end_time   = t.get_end_time()
                else:
                    t.end = t.get_start_time()
                    last_end_time = t.end
            else: # null start time
                if t.get_end_time() != None:
                    t.start         = t.get_end_time()
                    last_end_time   = t.get_end_time()
                else: # both null
                    t.start = last_end_time
                    t.end = t.start
                    last_end_time = t.end
        if isinstance(t,PuncRelation):
            t.start       =  last_end_time
            t.end         =  t.start
            last_end_time =  t.end
        if isinstance(t,SilRelation):
            t.start = last_end_time
            t.end   = tlist[i+1].get_start_time()
            if t.end == None:
                t.end = t.start
            last_end_time = t.end
        if isinstance(t,TraceRelation):
            t.start       = last_end_time
            t.end         = t.start
            last_end_time = t.end

        print t,last_end_time
        if t.end != last_end_time:
            raise Exception("last end time error")
        if t.end < t.start:
            raise Exception("t end is less than t start")
        if last_end_time == None:
            raise Exception("Null last end time")


