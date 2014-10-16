from __future__ import division


'''
	some tools to postprocess matches and remove false positives that slipped through
		the initial procedure.

	all filters return TRUE for GOOD matches.

'''
def short_mismatch_filter(match, max_short_len=10, max_ratio=0.3):

	total_align_len = sum([len(x) for x in match['alignment']])
    unaligns = sum([sum([a<0 for a in x]) for x in match['alignment']])
    if unaligns / total_align_len >= max_ratio and total_align_len <= 10:
    	return False 
    else:
    	return True