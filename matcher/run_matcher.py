from matcher import QuoteMatcher
from article_reader import ArticleReader
import os

import cPickle

TRANSCRIPT_ORDER = '/NLP/creativity/work/pres_addrs/output_whitehouse/transcript_data/whitehouse_transcript_order.pk'
TRANSCRIPTS = '/NLP/creativity/work/pres_addrs/output_whitehouse/transcript_data/whitehouse_transcripts.pk' 
spinn3r_dir = "/NLP/creativity/nobackup/results/"
stopword_file = '/NLP/creativity/work/pres_addrs/src_new/matcher/mysql_stop.txt'
OUTPUT_DIR = '/NLP/creativity/work/pres_addrs/output_whitehouse/match_data'

print 'loading all'
with open(TRANSCRIPT_ORDER, 'r') as f:
	order = cPickle.load(f)

with open(TRANSCRIPTS, 'r') as f:
	transcripts = cPickle.load(f)

qm = QuoteMatcher(order, transcripts, stopword_file=stopword_file)
ar = ArticleReader(qm, verbose=True)

count = 0

filelist = [os.path.join(spinn3r_dir, f) for f in os.listdir(spinn3r_dir) if f.endswith('.gz')]

print 'starting matching'
for f in filelist:
	cache = False
	if count == 1 or count == 10 or count % 10000 == 0:
		cache = True
	count += 1
	ar.read_spinn3r_file(f)
	if cache:
		print 'dumping all'
		with open(os.path.join(OUTPUT_DIR, 'matches.pk'), 'wb') as f:
			cPickle.dump(ar.matches, f)
		with open(os.path.join(OUTPUT_DIR, 'article_to_idx.pk'), 'wb') as f:
			cPickle.dump(ar.article_to_idx, f)
		with open(os.path.join(OUTPUT_DIR, 'idx_to_article.pk'), 'wb') as f:
			cPickle.dump(ar.idx_to_article, f)
		with open(os.path.join(OUTPUT_DIR, 'errors.pk'), 'wb') as f:
			cPickle.dump(ar.errors, f)
		cache = False
	num_matches = len(ar.matches)
	print str(count) + ' files read'
	print str(num_matches) + ' matches'

print str(len(ar.errors)) + ' errors'

print 'dumping all'
with open(os.path.join(OUTPUT_DIR, 'matches.pk'), 'wb') as f:
	cPickle.dump(ar.matches, f)
with open(os.path.join(OUTPUT_DIR, 'article_to_idx.pk'), 'wb') as f:
	cPickle.dump(ar.article_to_idx, f)
with open(os.path.join(OUTPUT_DIR, 'idx_to_article.pk'), 'wb') as f:
	cPickle.dump(ar.idx_to_article, f)
with open(os.path.join(OUTPUT_DIR, 'errors.pk'), 'wb') as f:
	cPickle.dump(ar.errors, f)
print 'done'