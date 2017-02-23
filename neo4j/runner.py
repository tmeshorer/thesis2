__author__ = 'Tomer'

import corpus
import query
import pandas as pd
import logging
import os

logger = logging.getLogger('curpus')
error_log = logging.getLogger('error')

def test_export_to_csv():
    dacts = query.all_dacts_q()
    dacts_list = []
    for x in dacts:
        dacts_list.append(x[0].properties)
    df = pd.DataFrame(dacts_list)
    df.to_csv("c:\\temp\\c.csv")


def load_db():
    corpus1 = corpus.SbCorpus(corpus.CORPUS_ROOT)
    corpus1.read_corpus_resources()
    builder = corpus.GraphBuilder()
    builder.make_csv_dir()
    builder.add_metadata(corpus1)
    count = 0

    for k, v in corpus1.dialog_nodes.iteritems():
        if not os.path.exists(corpus.CSV_DIR + v.id):
            # try:
            query.clean_all()
            corpus1.read_dialog_data(v)
            builder.add_dialog_timeline(v)
            return


def run():
    #read the corpus
    corpus1 = corpus.SbCorpus(corpus.CORPUS_ROOT)
    corpus1.read_corpus_resources()
    builder = corpus.GraphBuilder()
    builder.make_csv_dir()
    builder.add_metadata(corpus1)
    count = 0

    for k,v in corpus1.dialog_nodes.iteritems():
        if not os.path.exists(corpus.CSV_DIR + v.id):
            try:
                query.clean_all()
                corpus1.read_dialog_data(v)
                builder.add_dialog_timeline(v)
                logger.info("============================ before query ================")
                query.print_all()
                logger.info("==========================================================")
                query.run_q()
                query.to_csv(corpus.CSV_DIR + v.id)
                logger.info("============================ after clean ================")
                query.print_all()
                logger.info("==========================================================")
            except:
                error_log.error("Failed to handle dialog %s" % k)
               

    builder.mergecsv()

if __name__ == '__main__':
     run()
    