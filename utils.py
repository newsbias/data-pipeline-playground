import itertools
from collections import Counter
from nltk.corpus import stopwords
import re
import numpy as np
from nltk.tag import pos_tag

stop = stopwords.words('english')
NEWS_SOURCES = ['CNN', 'USA Today', 'Washington Post']

async def attach_id(id, fut):
    return (id, await fut)


def get_combinations(words, k):
    len_to_list_map = {}

    # Split input into a list of words
    n = len(words)

    if not k:
        k = n

    # Loop from 1 to k
    for i in range(1, k+1):

        # List to store strings comprised of i words
        l = set()

        # Loop through all words in input string
        for j in range(0, n-i+1):

            # Base string to add to
            s = ""

            # Add strings of i words to the list
            for z in range(j, j+i):
                s = s + words[z] + " "

            s = s.strip()
            l.add(s)
            if i in len_to_list_map:
                len_to_list_map[i] |= l
            else:
                len_to_list_map[i] = l

    return len_to_list_map

def clean(sent):
    sent = re.sub('[^A-Za-z0-9_ ]', '', sent)
    sent = sent.split()
    return [word for word in sent]

def get_keywords(articles):
    return [word for article in articles for word in separate_words(article) if word not in NEWS_SOURCES]


def separate_words(sent):
    sent = clean(sent)
    i = 0
    output = []
    tagged_sent = pos_tag(sent)
    while i != len(tagged_sent):
        word, pos = tagged_sent[i]
        prev_i = i

        while pos == 'NNP' and i < len(tagged_sent):
            i += 1
            if i < len(tagged_sent):
                word, pos = tagged_sent[i]

        name = ''
        if prev_i == i:
            name = tagged_sent[i][0]
            i = prev_i + 1
        else:
            name = ' '.join([x[0] for x in tagged_sent[prev_i:i]])

        if name not in stop and len(name) > 1:
            output.append(name)
    return output

# input is a list of strings
# output is a dictionary of list of strings, where the key in the dictionary is the length of the list returned by separate_words
def parse(list_of_words, k=None):
    output = {}

    for elt in list_of_words:
        elt = separate_words(elt)
        for size, combination in get_combinations(elt, k).items():
            if size not in output:
                output[size] = set()
            output[size].update(combination)
    return output


# (arg) sections: dictionary of sections to outlinks
# outer list is the index corresponding to the index of the section
# (arg) vocabulary: is just a list of strings.
# returns: list of keywords that appear in each section
def filter_keywords_by_section(sections, vocabulary):

    BAD_SECTIONS = ['External links', 'References', 'Bibliography', 'Notes', 'See also']

    # 1) filter out news articles from vocab
    # 2) only get the lowest level of info
    filtered = {}
    for topic, keywords in sections.items():
        if topic not in BAD_SECTIONS:
            sections[topic] = [keyword for keyword in sections[topic] if keyword in vocabulary]

    
    return dict(sorted(sections.items(), key=lambda s: len(s[1]), reverse=True)[:10])
    
    '''

    keywords_by_section_by_length = []
    for keywords in keywords_by_section:
        keywords_by_length = parse(keywords)
        if keywords_by_length:
            keywords_by_section_by_length.append(keywords_by_length)
    
    vocabulary_by_length = parse(vocabulary)

    filtered_keywords_by_section = []
    for filtered_keywords in keywords_by_section_by_length:
        import pdb
        pdb.set_trace()

        intersections = []
        for length, keywords in filtered_keywords.items():
            intersections.append(vocabulary_by_length[length].intersection(keywords))
        
        flattened_intersections = list(itertools.chain.from_iterable(intersections)) 
        filtered_keywords_by_section.append(flattened_intersections)
        '''