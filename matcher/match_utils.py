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







