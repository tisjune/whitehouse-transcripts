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
HYPHEN_TYPES = ["\xe2\x80\x94", " - ", " -- "] 
NUM_MAP = {'0':'zero', '1': 'one', '2':'two','3':'three','4':'four',
			'5':'five','6':'six','7':'seven','8':'eight','9': 'nine'} 
PUNCTUATION = '"&\'()+,-./:;<=>@[\\]^_`{|}~'


def no_punct(phrase):
	'''
		Strips punctuation from a phrase. Uses python's string.punctuation set, but 
                retains % and $s.
	'''
	return ' '.join(phrase.translate(string.maketrans("",""),PUNCTUATION).split())

def handle_hyphens(phrase):
	'''
		Standardizes hyphen formats.
	'''
	dehyphenated = phrase
	for hyphen_type in HYPHEN_TYPES:
		dehyphenated = dehyphenated.replace(hyphen_type, "- ")
	return dehyphenated

def standardize_formatting(phrase):
	'''
		Converts texts to standard format.
		Currently this tries to match format in speech transcripts.
	'''
	formatted_phrase = phrase
	formatted_phrase = formatted_phrase.replace(' per cent ', ' percent ')
	formatted_phrase = formatted_phrase.replace(' usd ', ' $')
	formatted_phrase = formatted_phrase.replace('%',' percent')
	formatted_phrase = re.sub(r'\d+ dollars', lambda x: '$'+x.group(0).split()[0], formatted_phrase)
	return formatted_phrase



def strip_dashes(phrase):
	
	to_use = phrase.replace('-', ' ')

	return to_use

def convert_to_display_array(phrase, formatfn = lambda x: x):
	'''
		Converts text to array of words after format standardization.
		Retains capitalization and punctuation.

		Arguments:
			formatfn (function, optional): custom function to further format phrase 
				before conversion.
	'''
	to_use = formatfn(phrase)
	return standardize_formatting(handle_hyphens(to_use)).split()

def convert_word(word):
	'''
		Strips capitalization and punctuation from word;
		also converts numerals to words if < 10.
	'''
	converted = word
	num_equiv = NUM_MAP.get(word, None)
	if num_equiv is not None:
		converted = num_equiv
	return no_punct(converted).lower()

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
	return [convert_word(word) for word in display_array]

def fetch_transcripts(transcript_dir):
	'''
		Reads transcripts from transcript_dir.
		Transcripts should be formatted as such:
			Transcript title
			Transcript timestamp (%Y-%m-%d %H:%M)
			Transcript text
		
		Returns:
			transcript_order:
				A list of transcript filenames ordered by transcript timestamp.
			transcript_text:
				A dictionary of transcript filename to various transcript representations:
					'display': display_array
					'match': match_array
					'bag': set of words in transcript
					'raw': raw text, formatted without capitalization and punctuation
					'timestamp': transcript timestamp
			
	'''
	transcript_order = []
	transcript_text = {}

	for transcript_name in os.listdir(transcript_dir):
		with open(os.path.join(transcript_dir,transcript_name)) as f:

			title = f.readline()
			date = dt.datetime.strptime(f.readline().strip(), TRANSCRIPT_TIMEFORMAT)
			date = date.replace(hour=0, minute=0) # dubious but I've noticed weird behaviour here.
			transcript_order.append((date, transcript_name))

			speech = f.read()
			transcript_dict = {}
			transcript_dict['timestamp'] = date

			display_array = convert_to_display_array(speech)
			match_array = convert_to_match_array(speech, display_array)
			raw_text = ' '.join(match_array)

			transcript_dict['display'] = display_array
			transcript_dict['match'] = match_array
			transcript_dict['bag'] = set(match_array)
			transcript_dict['raw'] = raw_text

			transcript_text[transcript_name] = transcript_dict

	transcript_order = sorted(transcript_order, key=lambda elem: elem[0])
	return transcript_order, transcript_text


def print_quote(quote, alignment, transcript_collection, transcript_name, extra='[]', omit='__'):
	'''
		Prints a quote as aligned to a transcript. 

		Quotes can either omit or add words to the original transcript text.
		Omissions are preceded and followed by characters specified in argument omit (default: '_')
		Additions are preceded and followed by characters specified in extra (default: '[]')

		Arguments:
			quote (str): original quote text
			alignment (tuple of int tuples): quote alignment specified as tuple(aligned indices, for each segment)
			transcript_collection: set of transcript texts as returned by fetch_transcript
			transcript_name (str): name of transcript aligned to
			extra (str): characters preceding and following additions made by quote
			omit (str): characters preceding and following text omitted by quote.

		Returns: str, a printable version of the quote.
	'''	
	segments = get_segments(quote)
	transcript_array = transcript_collection[transcript_name]['display']
	return '...'.join([print_segment(seg, align, transcript_array, extra, omit)
                       for seg, align in zip(segments, alignment)])

def print_segment(segment_text, segment_align, transcript_array, extra, omit):
    segment_array = convert_to_display_array(segment_text)
    if len(segment_array) != len(segment_align):
        segment_array = convert_to_match_array(segment_text, 
                                        formatfn = strip_dashes)
    print_str = ''
    last_positive_index = -1
    prev_index = None
    for i in range(len(segment_align)):
        seg_word = segment_array[i]
        if no_punct(seg_word) != '':
            align_index = segment_align[i]
            if align_index != -1:
                if prev_index == -1:
                    print_str += extra[1] + ' '
                if (last_positive_index < 0 
                    or align_index == last_positive_index + 1):
                    print_str += transcript_array[align_index] + ' '
                    last_positive_index = align_index
                else:
                    print_str +=  omit[0]+' '.join([transcript_array[x] for
                            x in range(last_positive_index +1, align_index)]) + omit[1] + ' '
                    print_str += transcript_array[align_index] + ' '
                    last_positive_index = align_index
            else:
                if prev_index != -1:
                    print_str += extra[0] + seg_word
                else:
                    print_str += ' '+seg_word
                
            prev_index = align_index
    if prev_index == -1:
    	print_str += extra[1]
    return print_str

def align(quote, transcript_text, transcript_array, sub_pen = -1, gap_pen = -1):
	'''
		Aligns a quote to a transcript, segment by segment (where segments delimited by '...').
		
		Arguments:
			quote (str): quote text
			transcript_text (str): transcript text (formatted by standardize_format)
			transcript_array (list of str): transcript word array (match_array)
			sub_pen (float, optional, default=-1): substitution penalty used by Needleman-Wunsch
			gap_pen (float, optional, default=-1): gap penalty used by Needleman-Wunsch

		Returns:
			alignment (list of int): list of indices into transcript_array where quote has matching words.
					an index of -1 indicates no match found.
			score (float): across segments, average of similarity score as returned by Needleman Wunsch.
	'''
	quote_segments = [x for x in quote.split('...') if len(no_punct(x))>0]
	alignment = []
	total_score = 0
	for segment in quote_segments:
		segment_alignment = align_segment(segment, transcript_text, transcript_array, sub_pen, gap_pen)
		alignment.append(segment_alignment[0])
		total_score += segment_alignment[1]
	score = total_score / len(quote_segments)
	return alignment, score

def get_segments(quote):
	return [x for x in quote.split('...') if len(x.strip())>0]

def align_segment(segment, transcript_text, transcript_array, sub_pen = -1, gap_pen = -1):
	segment_array = convert_to_match_array(segment)
	if ' '.join(segment_array) in transcript_text: #verbatim match
		result = align_verbatim(segment_array, transcript_array)
		return result
	else: #checks case where dashes are omitted i.e. middle-class vs middle class
		d_segment_array = convert_to_match_array(segment, formatfn = strip_dashes)
		if ' '.join(d_segment_array) in transcript_text:
			result = align_verbatim(d_segment_array, transcript_array)
			return result
		else: # aligns non-verbatim quotes.
			# checks case where dashes match format in transcript, and where dashes don't; 
			#	takes the best-scoring alignment.
			# may break pretty printing in future, but right now we know d_align_result
			# will contain more tokens than align_result
			align_result = align_paraphrase(segment_array, transcript_array, sub_pen, gap_pen)
			d_align_result = align_paraphrase(d_segment_array, transcript_array, sub_pen, gap_pen)
			if align_result[1] >= d_align_result[1]:
				return align_result
			else:
				return d_align_result


def align_quote(quote, transcript_array, is_verbatim, sub_pen = -1, gap_pen = -1):
	quote_array = convert_to_match_array(quote)
	d_quote_array = convert_to_match_array(quote, formatfn = strip_dashes)
	if is_verbatim:
		verbatim_result = align_verbatim(quote_array, transcript_array)
		if verbatim_result[1] == 0:
			return verbatim_result
		else:
			
			verbatim_result = align_verbatim(d_quote_array, transcript_array)
			if verbatim_result[1] == 0:
				return verbatim_result
			else:
				return None, None
	else:
		align_result = align_paraphrase(quote_array, transcript_array, sub_pen, gap_pen)
		d_align_result = align_paraphrase(d_quote_array, transcript_array, sub_pen, gap_pen)
		if align_result[1] >= d_align_result[1]:
			return align_result
		else:
			return d_align_result

def subarray_search(small_array, big_array, startindex):

	for i in range(startindex, len(big_array) - len(small_array) + 1):
	    if small_array == big_array[i:i+len(small_array)]:
	        return range(i, i+len(small_array))
	return None

def align_verbatim(quote_array, transcript_array):
	# aligns verbatim quotes. assumes that quote text is verbatim in transcript text.
	simple_match_result = subarray_search(quote_array, transcript_array, 0)

	if (simple_match_result):
		return tuple(simple_match_result), 0

	else: 
		shortened_quote_array = quote_array[1:-1]
		startindex = 1
		while startindex <= len(transcript_array) - len(quote_array):
			snip_match_result = subarray_search(shortened_quote_array, transcript_array, startindex)
			if snip_match_result:
				if (transcript_array[snip_match_result[0]-1].endswith(quote_array[0]) 
                    and transcript_array[snip_match_result[-1]+1].startswith(quote_array[-1])):
					return tuple(range(snip_match_result[0]-1, snip_match_result[-1]+2)), 0
				else:
					startindex = snip_match_result[0] + 1
			else:
				break
	                
        return None, None

	
def align_paraphrase(quote_array, transcript_array, sub_pen = -1, gap_pen = -1):
	'''
		Uses Needleman-Wunsch to align a quote to a transcript, returning tuple (alignment, similarity score).

		Note this is a modified version of NW to deal with aligning a short string to a substring of a longer string.

		In particular, gaps before and after the occurrence of the substring are not penalized.
	'''
		# initialization 
	sseq = [''] + quote_array
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




