import itertools
from term_frequency import separate_words
from utils import get_combinations

def parse(list_of_words, k = None):
	output = {}

	for elt in list_of_words:
		elt = separate_words(elt)
		for group in elt:
			output = get_combinations(elt, k, output)

	return output

# outlinks by section -> list of lists, where the inner-list is the outlinks. outer list is the index corresponding to the index of the section
# articles -> comes from get_most_common_words. just a list.
def intersection(outlinks_by_sect, keywords):
    section_keywords = []
	sections = [parse(outlinks) for outlinks in outlinks_by_sect]

    for section in sections:
        k = max(section.keys())

	    keywords_dic = parse(keywords, k)

	    section_keywords.append(list(itertools.chain.from_iterable([k.instersection(o) \
            for _, o in outlinks_dic.items() \
            for _, k in keywords_dic.items()])))

    return section_keywords
