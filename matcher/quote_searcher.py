import gzip, os
import datetime as dt 
from matcher import QuoteMatcher
import cPickle

NEWS_TIMEFORMAT = "%Y-%m-%d %H:%M:%S"

class ArticleReader(object):

	'''
		reads spinn3r articles, matches quotes within them,
		and keeps track of a dictionary of articles containing matching quotes.

		Arguments:

			quote_matcher: QuoteMatcher object 
			verbose (boolean, default=True)

		Structures:

			articles are formatted as dicts. important fields:
				{
					'url',
					'title',
					'content', 
					'quotes' (as tuples),
					'onsets' (as tuples; idx of each quote in content),
					'date' (as datetime)
				}

			article_to_idx: map of (article url, article content) to 
					index in idx_to_article
			idx_to_article: map of index to article 
			mentions: array of matches, where each match is of the following format:
				{
					'quote': quote text,
					'url': source url,
					'article_idx': index of article in idx_to_article,
					'transcript_name': filename of matched transcript, 
					'paragraph': index of paragraphs matched to
					'alignment': quote alignment (as tuple of ints),
					'similarity': sim b/n quote and transcript
				}
				version, paragraph and alignment are tuples: one entry for each segment of the quote.
			errors: array of quotes which threw errors during matching. 
				entries formatted as such:
					{
						'quote': quote text,
						'article': article
					}
	'''

	def __init__(self, quote_matcher, verbose=True):

		self.qm = quote_matcher

		self.verbose = verbose

		self._next_article_idx = 0

		self.article_to_idx = {}
		self.idx_to_article = {}

		self.mentions = []

		self.errors = []

	def read_spinn3r_file(self, filename):

		'''
			processes all articles in a spinn3r data file.

			Arguments:

				filename: you know...
		'''

		if self.verbose:
			print 'Reading ' + filename

		with gzip.open(filename, 'rb') as f:

			for line in f:

				article = self._load_article(line)
				self._read_article(article)


	def _load_article(self, line):

		article_dict = eval(line)

		strdate = article_dict['date']
		article_dict['date'] = dt.datetime.strptime(strdate, NEWS_TIMEFORMAT)

		quotes = []

		onsets = []

		raw_quote_list = article_dict['quotes']
		for elem in raw_quote_list:
			quotes.append(elem['quote'])
			onsets.append(elem['onset'])

		article_dict['quotes'] = tuple(quotes)
		article_dict['onsets'] = tuple(onsets)

		return article_dict

	def _read_article(self, article):

		article_key = (article['url'], article['content'])
		article_idx = self.article_to_idx.get(article_key, None)

		if article_idx:
			# save earliest version of article
			stored_date = self.idx_to_article[article_idx]['date']
			if article['date'] < stored_date:
				self.idx_to_article[article_idx] = article
		else:

			has_matching_quote = False

			for quote in article_dict['quotes']:

				try:
					match_result = self.qm.match_quote(quote, article['date'])
					if match_result is not None:
						has_matching_quote = True
						self.mentions.append({'quote': quote,
											  'url': article['url'],
											  'article_idx': this_article_idx,
											  'transcript_name': match_result['transcript_name'],
											  'paragraph': match_result['paragraph']
											  'alignment': match_result['alignment'],
											  'similarity': match_result['similarity']})

				except:
					self.errors.append({'quote': quote, 
										'article': article})
					if verbose:
						print quote

			if has_matching_quote is True:

				#only save to article base if we found a quote
				this_article_idx = self._next_article_idx
				self.article_to_idx[article_key] = this_article_idx
				self.idx_to_article[this_article_idx] = article
				self._next_article_idx += 1