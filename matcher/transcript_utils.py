from __future__ import division

import string
import os
import datetime as dt 
import numpy as np
import re

import match_utils as mu

TRANSCRIPT_TIMEFORMAT = "%Y-%m-%d %H:%M"

def get_first_pos(seq): 
	first_pos = seq[0]
	index = 0
	while (first_pos < 0):
		first_pos = seq[index]
		index += 1
	return first_pos

class TranscriptCollection(object): # I am bothered by how this is different from what I did to handle transcripts during alignment :(

	def __init__(self, transcript_dir):

		self.transcript_dir = transcript_dir

		self.transcript_order = []
		self.transcript_text = {}

		for transcript_name in os.listdir(transcript_dir):

			with open(os.path.join(transcript_dir,transcript_name)) as f:

				title = f.readline()
				date = dt.datetime.strptime(f.readline().strip(), TRANSCRIPT_TIMEFORMAT)
				date = date.replace(hour=0, minute=0) # dubious but I've noticed weird behaviour here.
				self.transcript_order.append((date, transcript_name))

				speech = f.read()

				paragraphs = speech.split('\n')

				para_array = [mu.convert_to_display_array(x) for x in paragraphs]

				transcript_dict = {}
				transcript_dict['paragraphs'] = para_array
				transcript_dict['timestamp'] = date

				self.transcript_text[transcript_name] = transcript_dict

		self.transcript_order = sorted(self.transcript_order, key=lambda elem: elem[0])


	def dump_all(self, outfile):

		with open(outfile, 'w') as f:
			for t in self.transcript_order:
				t_paras = self.transcript_text[t[1]]['paragraphs']

				display_strs = [' '.join(p) for p in t_paras]
				display_str = '\n'.join(display_strs)

				f.write(display_str + '\n')

	def format_jslda(self, outfile, by_paragraph = True):
		#docname\tpara_id\tparagraph maybe? not sure why what looks like para_id is listed twice in the sotu_small.txt example

		with open(outfile, 'w') as f:

			for t in self.transcript_order:

				tname = t[1]
				t_paras = self.transcript_text[tname]['paragraphs']

				if by_paragraph:
					

					para_id = 0

					for p in t_paras:

						display_str = ' '.join(p)

						para_name = tname + '_' + str(para_id)
						f.write(para_name + '\t' + tname + '\t' + display_str + '\n')

						para_id += 1

				else:

					display_strs = [' '.join(p) for p in t_paras]
					display_str = ' '.join(display_strs)

					f.write(tname + '\t' + tname + '\t' + display_str + '\n')




	def get_paragraph_id(self, alignment):

		transcript_name = alignment[1]

		para_array = self.transcript_text[transcript_name]['paragraphs']

		align_start = get_first_pos(alignment[0][-1])

		para_id = 0 
		word_num = 0

		for p in para_array:

			word_num += len(p)

			if word_num > align_start:

				return para_id

			para_id += 1

		return para_id