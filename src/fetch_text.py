# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
from datetime import datetime
import tldextract
import urllib2
import os
import re
import string

testurl0 = 'http://www.whitehouse.gov/the-press-office/2014/10/03/remarks-president-town-hall-manufacturing'
testurl1 = 'http://www.whitehouse.gov/the_press_office/Remarks-by-the-President-at-a-fundraiser-for-Senator-Harry-Reid-5/26/2009'
testurl2 = 'http://www.whitehouse.gov/the-press-office/2012/06/27/remarks-president-picnic-members-congress'
testurl3 = 'http://www.whitehouse.gov/the_press_office/Remarks-by-the-President-on-the-Fiscal-Year-2010-Budget'
testurl4 = 'http://www.whitehouse.gov/the-press-office/2013/02/12/remarks-president-state-union-address'
testurl5 = 'http://www.whitehouse.gov/the-press-office/2014/10/04/weekly-address-we-do-better-when-middle-class-does-better'
testurl6 = 'http://www.whitehouse.gov/the-press-office/2014/10/03/remarks-first-lady-michelle-obama-martha-coakley-governor-rally'

LISTING_ROOT_ADDR = "http://www.whitehouse.gov/briefing-room/speeches-and-remarks?page="
ROOT_ADDR = 'http://www.whitehouse.gov'
#OUTPUT_DIR = "/NLP/creativity/work/pres_addrs/whitehouse_texts/texts"
#OUTPUT_DIR = "/NLP/creativity/work/pres_addrs/whitehouse_texts/test"
OUTPUT_DIR = "/NLP/creativity/work/pres_addrs/whitehouse_texts/transcripts"
DEBUG_DIR = "/NLP/creativity/work/pres_addrs/whitehouse_texts/debug"

CONTENT_DIV_CLASS = 'extend-page body-text clearfix clear press-article node-content'
INPUT_TIMEFORMAT = '%B %d, %Y'
DISPLAY_TIMEFORMAT = '%Y-%m-%d %H:%M'
TIME_RE = r'\d\d?:\d\d'
DATE_RE = r'(\w+ \d\d?, \d\d\d\d)'
PUNCTUATION = { 0x2018:0x27, 0x2019:0x27, 0x201C:0x22, 0x201D:0x22 }
PUNCT_TOREAD = '.?!-:"'
END = 'END'

def fetch_urls_from_listing(url):
	
	html = urllib2.urlopen(url).read()
	soup = BeautifulSoup(html)
	
	entry_list = soup.find('ul', class_='entry-list')
	
	listings = entry_list.find_all('a')
	
	speech_urls = []
	for l in listings:
		speech_urls.append(ROOT_ADDR + l['href'])
	return speech_urls

def format_filename(url):

	return '_'.join(url.split('/')[4:])

def format_date(datestring):
	return datetime.strptime(datestring.strip(),INPUT_TIMEFORMAT).strftime(DISPLAY_TIMEFORMAT)

def cleanup_text(text):

	if not text.isspace():
		return re.sub(r'\([^)]*\)', '', unicode(text)).translate(PUNCTUATION)\
		.replace('--  --','').strip()
	else:
		return '\n'

def start_reading(text):

	no_spaces = text.strip()
	if no_spaces:

		#doesn't want to pull annoying weekly address summary, or HH:MM A.M.
		#but we're assuming everything with punct at the end is otherwise a real paragraph.
		return ('WASHINGTON' not in no_spaces 
			and not re.findall(TIME_RE, text) 
			and 'Washington' not in no_spaces
			and no_spaces[-1] in PUNCT_TOREAD)
	else:
		return False

def fetch_transcript(url):

	html = urllib2.urlopen(url).read()
	soup = BeautifulSoup(html)

	title = soup.find('title').contents[0].split('|')[0].encode('utf8')
	date = None
	text = []

	content = soup.find('div', class_ = 'legacy-content')

	if not content:
		# not legacy
		content = soup.find('div', class_=CONTENT_DIV_CLASS).find('div',attrs={'id':'content'})
		date_raw = content.find('div',class_='date')
		if date_raw:
			date = format_date(date_raw.contents[0])
	all_text = content.findAll(text = True)

	read = False
	for x in all_text:
		clean = cleanup_text(x)
		if END in clean:
			break
		if not date:
			date_searched = re.search(DATE_RE, clean)
			if date_searched:
				date = format_date(date_searched.group(1))

		if read:
			if clean.isspace():
				if len(text) == 0 or not text[-1].isspace():
					text.append(clean)
			else:
				text.append(clean)
		else:
			read = start_reading(clean)
			if read:
				text.append(clean)

	filename = format_filename(url)
	towrite = ''.join(text).encode('utf8')

	if title and date and not towrite.isspace():

		with open(os.path.join(OUTPUT_DIR, filename), 'w') as f:
			f.write(title + '\n')
			f.write(date + '\n')
			f.write(towrite)
		return 'success'

	else:
		return url

##############################################


failures = []
crashes = []


for i in range(327):

	print 'fetching from listing '+str(i) + '...'

	urls = fetch_urls_from_listing(LISTING_ROOT_ADDR + str(i))

	for url in urls:
		try:
			result = fetch_transcript(url)
			if result is not 'success':
				print url + ' fail '
				failures.append(url)
		except:
			print url + ' crash '
			crashes.append(url)

print str(len(failures)) + ' failures'
print str(len(crashes)) + ' crashes'

with open(os.path.join(DEBUG_DIR,'failures.pk'), 'wb') as f:
	cPickle.dump(failures, f)

with open(os.path.join(DEBUG_DIR,'crashes.pk'), 'wb') as f:
	cPickle.dump(crashes, f)