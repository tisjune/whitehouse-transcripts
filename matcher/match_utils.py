'''
	Standard functions to do string processing.

	Some specific things this tries to handle:

	1. Standardizes how hyphens look 
		(everything of the form word1 - word2 gets turned into 
			word1- word2)
	2. Expresses numbers, $, % in a standard way (see NUM_MAP, standardize_formatting)
	3. Tokenizes text into arrays of words, for display and string alignment purposes.
	4. Reads in sets of transcripts and orders them by date.
	5. Aligns quotes to transcripts.

'''

from __future__ import division
import string
import os
import datetime as dt 
import numpy as np
import re 


TRANSCRIPT_TIMEFORMAT = "%Y-%m-%d %H:%M"
NEWS_TIMEFORMAT = "%Y-%m-%d %H:%M:%S"
HYPHEN_TYPES = ["\xe2\x80\x94", " - ", "\xe2\x80\x93",'\xe2\x80\x92'," -- "] 
NUM_MAP = {'0':'zero', '1': 'one', '2':'two','3':'three','4':'four',
			'5':'five','6':'six','7':'seven','8':'eight','9': 'nine'} 
PUNCTUATION = '"&\'()+,-./:;<=>@[\\]^_`{|}~'


def _no_punct(phrase):
	#retains % and $
	return ' '.join(phrase.translate(string.maketrans("",""),PUNCTUATION).split())

def _handle_hyphens(phrase):
	#sort of valiant attempt to manage hyphens
	dehyphenated = phrase
	for hyphen_type in HYPHEN_TYPES:
		dehyphenated = dehyphenated.replace(hyphen_type, "- ")
	return dehyphenated

def standardize_formatting(phrase):
	'''
		Converts texts to standard format.
		Currently this tries to match format in speech transcripts.
	'''
	formatted_phrase = _handle_hyphens(phrase)
	formatted_phrase = formatted_phrase.replace('\xe2\x80\xa6', '... ').replace('\xc2\xa0', '')
	formatted_phrase = formatted_phrase.replace(' per cent ', ' percent ')
	formatted_phrase = formatted_phrase.replace(' usd ', ' $')
	formatted_phrase = formatted_phrase.replace('%',' percent')
	formatted_phrase = re.sub(r'\d+ dollars', lambda x: '$'+x.group(0).split()[0], formatted_phrase)
	return formatted_phrase

def convert_to_display_array(phrase, formatfn = lambda x: x):
	'''
		Converts text to array of words after format standardization.
		Retains capitalization and punctuation.

		Arguments:
			formatfn (function, optional): custom function to further format phrase 
				before conversion.
	'''
	to_use = formatfn(phrase)
	return standardize_formatting(to_use).split()

def _convert_word(word):
	
	#Strips capitalization and punctuation from word;
	#also converts numerals to words if < 10.

	converted = word
	num_equiv = NUM_MAP.get(word, None)
	if num_equiv is not None:
		converted = num_equiv
	return _no_punct(converted).lower()

def convert_to_match_array(phrase, display_array=None, formatfn = lambda x: x):
	'''
		Converts text to array of words for string alignment; strips
		capitalization and punctuation.

		Arguments:
			display_array (list of str, optional): pre-existing display_array to convert
			formatfn (function, optional): performs further formatting on text before conversion.
	'''
	if display_array is None:
		display_array = convert_to_display_array(phrase, formatfn)
	return [_convert_word(word) for word in display_array]



def segment_quote(quote):

	segments = quote.split('...')
	seg_arrs = [convert_to_match_array(seg) for seg in segments]

	processed_segments = []
	to_append = []
	for curr_seg in seg_arrs:
		if len(curr_seg) > 0:
			if len(curr_seg) <= 2:
				to_append += curr_seg
			else:
				to_append += curr_seg
				processed_segments.append(to_append)
				to_append = []
	if len(to_append) > 0:
		if len(to_append) <= 2 and len(processed_segments) > 0:
			processed_segments[-1] += to_append
		else:
			processed_segments.append(to_append)

	return [tuple(seg) for seg in processed_segments]


def _subarray_search(small_array, big_array, startindex):

	for i in range(startindex, len(big_array) - len(small_array) + 1):
	    if small_array == big_array[i:i+len(small_array)]:
	        return range(i, i+len(small_array))
	return None

def align_verbatim(quote_array, transcript_array):
	# aligns verbatim quotes. assumes that quote text is verbatim in transcript text.
	simple_match_result = _subarray_search(quote_array, transcript_array, 0)

	if (simple_match_result):
		return tuple(simple_match_result)

	else: 
		shortened_quote_array = quote_array[1:-1]
		startindex = 1
		while startindex <= len(transcript_array) - len(quote_array):
			snip_match_result = _subarray_search(shortened_quote_array, transcript_array, startindex)
			if snip_match_result:
				if (transcript_array[snip_match_result[0]-1].endswith(quote_array[0]) 
                    and transcript_array[snip_match_result[-1]+1].startswith(quote_array[-1])):
					return tuple(range(snip_match_result[0]-1, snip_match_result[-1]+2)), 0
				else:
					startindex = snip_match_result[0] + 1
			else:
				break
	                
        return None


def load_stopword_set(stopword_filename = 'mysql_stop.txt'):
	stopword_set = set()
	with open(stopword_filename, 'r') as f:
		for line in f.readlines():
			stopword_set.add(line.strip())
	return stopword_set

def match_segment_to_paragraph(segment_arr, paragraph_dict, stopword_set,
								min_fuzz_len, word_ratio):
	segment_arr = list(segment_arr)
	raw_text = ' '.join(segment_arr)
	alignment = None

	# try verbatim match


	if raw_text in paragraph_dict['raw']:
		alignment = align_verbatim(segment_arr, paragraph_dict['match'])
	if alignment:
		return (alignment, 0)

	elif len(segment_arr) < min_fuzz_len:

		return (None, None)

	# try fuzzy match

	# see if enough words present
	segment_words = set(segment_arr) - stopword_set
	if len(segment_words) == 0:
		return (None, None)
	intersect_words = segment_words.intersection(paragraph_dict['words'])
	intersect_ratio = len(intersect_words) / len(segment_words)

	if intersect_ratio >= word_ratio:

		alignment, score = align_paraphrase(segment_arr, paragraph_dict['match'])
		return (alignment, score)
	else:
		return (None, None)

def align_paraphrase(quote_array, transcript_array, sub_pen = -1, gap_pen = -1):
	'''
		Uses Needleman-Wunsch to align a quote to a transcript, returning tuple (alignment, similarity score).

		Note this is a modified version of NW to deal with aligning a short string to a substring of a longer string.

		In particular, gaps before and after the occurrence of the substring are not penalized.
	'''
		# initialization 
	sseq = [''] + list(quote_array)
	bseq = [''] + transcript_array
	slen = len(sseq)
	blen = len(bseq)
	nw_matrix = np.zeros((slen, blen))
	nw_matrix[:,0] = gap_pen * np.array(range(0, slen))

	# score
	#return nw_matrix
	for i in range(1, slen):
		for j in range(1, blen):
			subcost = 0 if sseq[i]==bseq[j] else sub_pen
			nw_matrix[i,j] = max(nw_matrix[i-1,j-1]+subcost, 
                                nw_matrix[i-1,j]+ gap_pen, 
                                nw_matrix[i,j-1] + gap_pen)
	max_ind_rev = np.argmax(nw_matrix[-1,:][::-1])
	max_ind = blen - max_ind_rev - 1
	max_score = nw_matrix[-1, max_ind]
	weighted_score = max_score/len(quote_array)
	align_vect = [0] * (slen-1)
	i = slen - 1
	j = max_ind
	while (i > 0 and j > 0):
		if (j > 0 and nw_matrix[i,j] == nw_matrix[i,j-1] + gap_pen):
			j -= 1
		elif (i > 0 and nw_matrix[i,j] == nw_matrix[i-1, j] + gap_pen):
			align_vect[i-1] = -1
			i -= 1
		else:
			subcost = 0 if sseq[i]==bseq[j] else sub_pen
			align_vect[i-1] = -1 if subcost < 0 else j-1
			i -= 1
			j -= 1
	return tuple(align_vect), weighted_score