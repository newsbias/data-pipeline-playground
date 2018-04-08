import itertools
from collections import Counter
from nltk.corpus import stopwords
import re
import numpy as np
from nltk.tag import pos_tag

stop = stopwords.words('english')

async def attach_id(id, fut):
    return (id, await fut)


def get_combinations(words, k, output):
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



def get_keywords(articles):
    return set(np.array(Counter(
            re.sub('[^A-Za-z0-9_ ]', '', word)
            for article in articles
            for word in separate_words(article)
            if word not in stop and len(word) > 1
    ).most_common(100))[:, 0])


def separate_words(sent):
    i = 0
    output = []
    tagged_sent = pos_tag(sent.split())
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

        output.append(name)
    return output

# input is a list of strings
# output is a dictionary of list of strings, where the key in the dictionary is the length of the list returned by separate_words
def parse(list_of_words, k=None):
    output = {}

    for elt in list_of_words:
        elt = separate_words(elt)
        for group in elt:
            combinations = get_combinations(elt, k, output)
            for combination in combinations:
                size = len(combination)
                if size not in output:
                    output[size] = []
                output[size].append(combination)

    return output


# (arg) outlinks by section: is a list of lists, where the inner-list is the outlinks.
# outer list is the index corresponding to the index of the section
# (arg) vocabulary: is just a list of strings.
# returns: list of keywords that appear in each section
def filter_keywords_by_section(keywords_by_section, vocabulary):

    keywords_by_section_by_length = [parse(keywords) for keywords in keywords_by_section]
    vocabulary_by_length = parse(vocabulary)

    filtered_keywords_by_section = []
    for filtered_keywords in keywords_by_section_by_length:

        intersections = []
        for length, keywords in filtered_keywords.items():
            intersections.append(vocabulary_by_length[length].intersection(keywords))
        
        flattened_intersections = list(itertools.chain.from_iterable(intersections)) 
        filtered_keywords_by_section.append(flattened_intersections)

    return filtered_keywords_by_section
