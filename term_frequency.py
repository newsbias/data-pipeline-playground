from collections import Counter
from nltk.corpus import stopwords
import re
import numpy as np
from nltk.tag import pos_tag

stop = stopwords.words('english')

def get_most_common_words(articles):
    return set(np.array(Counter([\
    re.sub('[^A-Za-z0-9_ ]', '', word) \
        for article in articles \
            for word in separate_words(article['title']) \
                if word not in stop and len(word) > 1\
    ]).most_common(100))[:,0])


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
