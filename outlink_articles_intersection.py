import itertools
from term_frequency import separate_words

def get_combinations(elt, k):
	words = elt.split()
	if not k:
		k = len(words)
	# do work

def parse(list_of_lists, k = None):
	output = []
	for list in list_of_lists:
		for elt in list:
			elt = separate_words(elt)
			for group in elt:
				output.append(get_combinations(elt, k))

	return output

def get_outlinks(outlinks):


def intersection(outlinks, articles):
	outlinks_dic = parse(outlinks)
	k = max(outlinks_dic.keys())

	articles_dic = parse(articles, k)

	list(itertools.chain.from_iterable([a.instersection(o) for _, o in outlinks_dic.items() for _, a in articles_dic.items()]))
