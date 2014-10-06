from __future__ import division

import string
import os
import datetime as dt 
import numpy as np
import re

import match_utils as mu

TRANSCRIPT_TIMEFORMAT = "%Y-%m-%d %H:%M"

def load_transcript_collection(transcript_directory, stopword_file = 'mysql_stop.txt',
					default_speaker = 'THE PRESIDENT'):
	'''
		Loads a collection of transcripts, for quote matching.

		Arguments:
			transcript_directory: directory where transcripts are located
			stopword_file (default='mysql_stop.txt'): list of stop words
			default_speaker (default='THE PRESIDENT'): identity of speaker 
				if we cannot infer anyone else

		Returns:

			order: list of (transcript filename, date) in chronological order

			transcripts: dict of transcript filename to transcript data:

				{
					'title': title of speech,
					'date': timestamp of speech,
					'paragraphs': list of paragraphs in transcript
				}

				A paragraph is stored as the following dict:
					{
						'raw': raw text (lowercase),
						'display': list of words in paragraph. 
							used to synchronize display with matching.
						'match': list of words in transcript,
							stripped of paragraph and capitalization.
							used for quote matching.
						'words': set of words in paragraph.
						'speaker': speaker of paragraph (inferred & hopefully correct!)
					}
	'''
	stopword_set = set()
	with open(stopword_file, 'r') as f:
		for line in f.readlines():
			stopword_set.add(line.strip())

	order = []
	transcripts = {}

	count = 0

	for filename in os.listdir(transcript_directory):

		if count % 250 == 0:
			print count
		count += 1

		with open(os.path.join(transcript_directory, filename)) as f:

			title = f.readline()
			title = title.strip()
			date_raw = f.readline()
			date = dt.datetime.strptime(date_raw.strip(), TRANSCRIPT_TIMEFORMAT)
			order.append((filename, date))

			speech = f.read()
			paragraph_text = speech.split('\n')

			paragraphs = []

			curr_speaker = default_speaker
			for paragraph in paragraph_text:

				if 'Please see below for corrections' in paragraph:
					continue

				if paragraph and not paragraph.isspace():

					#find speaker
					if paragraph[0] == 'Q' and len(paragraph) > 1 \
						and paragraph[1].isspace():
						curr_speaker = 'Q'
						paragraph = paragraph[2:]

					split_for_speaker = paragraph.split(':')

					if len(split_for_speaker) > 1:
						potential_speaker = split_for_speaker[0]
						if potential_speaker.isupper():
							curr_speaker = potential_speaker
							speech_index = 1
						else:
							speech_index = 0
					else:
						speech_index = 0

					#process text

					speech_text = split_for_speaker[speech_index]

					display_array = mu.convert_to_display_array(speech_text)
					if len(display_array) == 0:
						continue
					if display_array[0] == 'Q':
						curr_speaker = 'Q'
					if display_array[0].isdigit() and len(paragraphs) == 1:
						continue

					match_array = mu.convert_to_match_array(speech_text)
					raw_text = ' '.join(match_array)
					words = set(match_array) - stopword_set

					pdict = {}
					pdict['raw'] = raw_text
					pdict['display'] = display_array
					pdict['match'] = match_array
					pdict['words'] = words
					pdict['speaker'] = curr_speaker
					
					paragraphs.append(pdict)

			tdict = {}
			tdict['title'] = title
			tdict['date'] = date
			tdict['paragraphs'] = paragraphs

			transcripts[filename] = tdict

	order = sorted(order, key=lambda elem: elem[1])
	return order, transcripts	 

