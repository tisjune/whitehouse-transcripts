from __future__ import division
import datetime as dt 
import os, string, collections, cPickle, bisect
import match_utils as mu 



class QuoteMatcher:

	MIN_LEN = 6
	MIN_FUZZ_LEN = 7
	MAX_INTERVAL = dt.timedelta(days=7)
	GAP_PEN = -1
	SUB_PEN = -1
	ACCEPT_THRESHOLD = -.1

	def __init__(self, transcript_order, transcript_collection,
		stopword_file = 'mysql_stop.txt', sim_tolerance = -.4, word_ratio = .75, verbose = 0):

		self.order = [x[0] for x in transcript_order]

		self.times = [x[1] for x in transcript_order]
		self.transcripts = transcript_collection

		self.stopwords = mu.load_stopword_set(stopword_file)

		self.tol = sim_tolerance
		self.word_ratio = word_ratio

		self.verbose = verbose

		# (segment as tup, transcriptname, paragraph num) -> {alignment, similarity}
		self.seg_para_cache = {}

		# (segment as tup, transcriptname) -> {alignment, paragraphnum, similarity}
		self.seg_transcript_cache = {}

		# (quote text, transcriptname) -> {alignment, paragraphnum, similarity}
		self.quote_transcript_cache = {}

		# (quote text, timestamp) -> {paragraph, alignment, similarity, transcript_name}
		self.quote_time_cache = {}

	def match_quote(self, quote, timestamp): # decomposition: who does that?
		if quote[0] == '?':
			# spinn3r doesn't unicode?!?
			return None

		#search cache

		cached_quote_result = self.quote_time_cache.get((quote,timestamp), None)

		if cached_quote_result is not None:
			if cached_quote_result['similarity'] >= self.tol:
				return cached_quote_result
			else:
				return None
		segment_arr = mu.segment_quote(quote)

		# check len req
		if max([len(x) for x in segment_arr]) < self.MIN_LEN:
			self.quote_time_cache[(quote, timestamp)] = {'similarity': None}
			return None
		# get timespan
		latest_transcript_index = bisect.bisect_left(self.times, timestamp) - 1
		earliest_transcript_index = bisect.bisect_left(self.times, timestamp - self.MAX_INTERVAL)

		if latest_transcript_index < 0 or earliest_transcript_index >= len(self.times):
			self.quote_time_cache[(quote, timestamp)] = {'similarity': None}
			return None

		# now that we know quote satisfies basic time and len, search thru transcripts...

		search_range = range(latest_transcript_index, earliest_transcript_index - 1, -1)
		best_align = None
		best_paras = None
		best_score = None
		best_transcript = None
		
		for i in search_range:

			curr_tname = self.order[i]

			curr_align = None
			curr_paras = None

			# first, see if we already matched quote to this transcript
			cached_quote_result = self.quote_transcript_cache.get((quote,curr_tname), None)
			if cached_quote_result is not None:
				curr_score = cached_quote_result['similarity']

				# definitely a match
				if curr_score >= self.ACCEPT_THRESHOLD:
					result_dict = {}
					result_dict['transcript'] = curr_tname
					result_dict['paragraph'] = cached_quote_result['paragraph']
					result_dict['alignment'] = cached_quote_result['alignment']
					result_dict['similarity'] = curr_score

					self.quote_time_cache[(quote, timestamp)] = result_dict

					return result_dict

				# it beats the current record...
				elif curr_score >= best_score and curr_score >= self.tol:
					best_score = curr_score
					best_align = cached_quote_result['alignment']
					best_paras = cached_quote_result['paragraph']
					best_transcript = curr_tname
				continue

			# now we make the effort to match each segment.
			transcript = self.transcripts[curr_tname]

			curr_align = [None] * len(segment_arr)
			curr_paras = [None] * len(segment_arr)
			min_seg_score = None

			# check if we already cached some segments to this transcript
			seg_break = False
			for j in range(len(segment_arr)):
				curr_seg = segment_arr[j]
				cached_seg_result = self.seg_transcript_cache.get((curr_seg, curr_tname), None)
				if cached_seg_result is not None:
					cached_score =  cached_seg_result['similarity']

					# if we see seg with low tol then the entire quote can't match the transcript
					if cached_score < self.tol:
						seg_break = True
						break  
					else:

						# keep track of the cached segment
						curr_align[j] = cached_seg_result['alignment']
						curr_paras[j] = cached_seg_result['paragraph']
						if min_seg_score is None or cached_score < min_seg_score:
							min_seg_score = cached_score 
			# move on!
			if seg_break:
				self.quote_transcript_cache[(quote, curr_tname)] = {'similarity': None}
				continue

			# now we make the effort to find all uncached segments.
			paragraphs = transcript['paragraphs']

			for j in range(len(segment_arr)):

				# but of course we don't do anything for things we already cached!
				if curr_align[j] is not None:
					continue 

				curr_seg = segment_arr[j]

				# keep track of the best seg -> para align.
				best_para_align = None
				best_para = None
				best_para_score = None

				for k in range(len(paragraphs)):
					

					# we check the cache first
					cached_para_result = self.seg_para_cache.get((curr_seg, curr_tname, k), None)
					if cached_para_result is not None:

						cached_score = cached_para_result['similarity']

						# if exact match, then we found the best paragraph so quit
						if cached_score == 0:
							best_para_align = cached_para_result['alignment']
							best_para = k
							best_para_score = 0
							break

						# definitely not a match
						elif cached_score < self.tol:
							continue

						# we beat the current best, so take note
						elif cached_score >= best_para_score:

							best_para_align = cached_para_result['alignment']
							best_para = k
							best_para_score = cached_score
					
					else:
						# we are forced to work now
						curr_para = paragraphs[k]
						align, score = mu.match_segment_to_paragraph(curr_seg,
											curr_para, self.stopwords, self.MIN_FUZZ_LEN,
											self.word_ratio)

						# cache result
						self.seg_para_cache[(curr_seg, curr_tname, k)] = {
											'alignment': align,
											'similarity': score
											}

						# we hit a perfect match! so we don't have to look at any more paras.
						if score == 0:
							best_para_align = align
							best_para = k
							best_para_score = score
							
							break
						# we beat the record, so take note.
						elif score >= self.tol and score >= best_para_score:
							best_para_align = align
							best_para = k
							best_para_score = score		

				# we finished checking seg against the transcript! let's see what we've found...

				# keep track of the alignment score. recall this is the min of 
					# each indiv segs score.
				if min_seg_score is None or best_para_score < min_seg_score:

					min_seg_score = best_para_score

				self.seg_transcript_cache[(curr_seg, curr_tname)] = {
						'alignment': best_para_align,
						'paragraph': best_para,
						'similarity': best_para_score
					}
				if best_para_score >= self.tol:
					curr_align[j] = best_para_align
					curr_paras[j] = best_para
				else:
					# the entire quote cannot match the transcript.
					seg_break = True
					break 


			# we give up on this transcript. move on.
			if seg_break:
				self.quote_transcript_cache[(quote, curr_tname)] = {'similarity': None}
				continue

			# now we've finally matched all segments.

			self.quote_transcript_cache[(quote, curr_tname)] = {
					'alignment': curr_align,
					'paragraph': curr_paras,
					'similarity': min_seg_score
				}
			
			if min_seg_score >= self.tol and min_seg_score > best_score:

				best_align = curr_align
				best_paras = curr_paras
				best_transcript = curr_tname
				best_score = min_seg_score

			# we definitely have a match with this transcript, so we don't
				# need to look at any other transcripts.
			if min_seg_score >= self.ACCEPT_THRESHOLD:
				break
		# and now we're done with the entire set of transcripts. let's see what we find ...
		result_dict = {
				'alignment': best_align,
				'paragraph': best_paras,
				'similarity': best_score,
				'transcript': best_transcript
			}
		self.quote_time_cache[(quote, timestamp)] = result_dict
		if best_score >= self.tol:
			return result_dict
		else:
			return None





