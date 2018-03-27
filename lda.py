import numpy as np

from nltk.corpus import stopwords
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from nltk.tag import pos_tag

from gensim import corpora
from gensim.models import LdaModel

class Processor:
	def __init__(self):
		self.stemmer = PorterStemmer()
		self.stop = stopwords.words('english')

	def get_tokens(self, text):

		tokens = [ self.stemmer.stem(word) \
					for sent in sent_tokenize(text) \
						for word in word_tokenize(sent) \
							if word not in self.stop \
							and len(word) > 2 ]
		return tokens


def filter_extremes(texts):

	dictionary = corpora.Dictionary(texts)

	dictionary.filter_extremes(no_below=1, no_above=0.8)

	return [dictionary.doc2bow(text) for text in texts], dictionary

def process(texts):
	processor = Processor()

	tokens = [processor.get_tokens(text) for text in texts]

	corpus, dictionary = filter_extremes(tokens)
	return corpus, dictionary

def do_cluster(obj):
	texts = [article['text'] + article['title'] for article in obj]
	corpus, dictionary = process(texts)

	model = LdaModel(
		corpus,
		num_topics=5,
		id2word=dictionary,
	    update_every=3,
	    chunksize=1000,
	    passes=10
	)


	topic_matrix = model.show_topics(formatted=False)
	clusters = {}
	for i, topic in enumerate(topic_matrix):
		clusters[i] = {"keywords": [str(word) for word, _ in topic[1]], "articles": []}

	for i, document in enumerate(corpus):

		cluster = np.argmax(np.array(model.get_document_topics(document))[:,1])
		clusters[cluster]['articles'].append(obj[i])


	return clusters
