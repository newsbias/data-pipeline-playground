import numpy as np

from nltk.corpus import stopwords
from nltk import sent_tokenize
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from nltk.tag import pos_tag

from gensim import corpora
from gensim.models import LdaModel

class Processor:
	def __init__(self, query):
		self.stemmer = PorterStemmer()
		self.stop = stopwords.words('english')
		self.query = query

	def get_tokens(self, text):

		accepted_pos = ['NNP', 'NNS']

		tokens = [ word
					for sent in sent_tokenize(text) \
						for word, pos in pos_tag(word_tokenize(sent)) \
							if pos in accepted_pos and \
							word not in self.query \
							and len(word) > 2]
		return tokens


def do_cluster(obj, query):
	texts = [article['title'] for article in obj]

	processor = Processor(query)

	tokens = [processor.get_tokens(text) for text in texts]


	dictionary = corpora.Dictionary(tokens)
	corpus = [dictionary.doc2bow(text) for text in texts]

	num_clusters = len(texts) / 5
	model = LdaModel(
		corpus,
		num_topics=num_clusters,
		id2word=dictionary,
	    update_every=5,
	    chunksize=10000,
	    passes=50
	)

	# size 10
	topic_matrix = model.show_topics(formatted=False, num_topics=num_clusters)

	clusters = [{"keywords": [str(word) for word, _ in topic[1]], "articles": []} for topic in topic_matrix]

	for i, document in enumerate(corpus):

		topic = np.array(model.get_document_topics(document))
		cluster = int(topic[np.argmax(topic[:,1])][0])

		clusters[cluster]['articles'].append(obj[i])

	return clusters
