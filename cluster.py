from datetime import datetime
from nltk.corpus import stopwords
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AffinityPropagation
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np



def preprocess(text):
    stemmer = PorterStemmer()
    stop = stopwords.words('english')
    tokens = [tok for tok in word_tokenize(text.lower())
              if tok not in stop]
    tokens_stemmed = [stemmer.stem(tok) for tok in tokens]
    return tokens_stemmed


def cluster_articles(articles):
    clusters = []
    i = 0
    if len(articles) > 0:
        tfidf = TfidfVectorizer(tokenizer=preprocess, norm='l2', smooth_idf=True)

        titles = [article["text_content"] for article in articles]

        X_tfidf = tfidf.fit_transform(titles).toarray()

        # print("transformed tf-idf")
        # print(len(X_tfidf), len(X_tfidf[0]), X_tfidf)

        # print("feature names")
        # print(len(tfidf.get_feature_names()))

        # OG Numbers that were modded preference=-4, damping=0.95
        '''
        ap = AffinityPropagation(
                damping=0.95, max_iter=4000,
                convergence_iter=400, copy=True,
                affinity='euclidean', verbose=True)
        '''
        hc = AgglomerativeClustering(linkage='complete', affinity='cosine', n_clusters=7)

        C = hc.fit_predict(X_tfidf)
        # print("shape: tfidf, AP predicted")
        # print(X_tfidf.shape, C.shape)
        # print("clusters", len(C))
        # print(hc.labels_)

        num_clusters = max(hc.labels_) + 1

        for c in range(num_clusters):

            cluster = {
                "articles": [articles[member] for member in np.where(hc.labels_ == c)[0]],
                "summarized": False,
                "_id": c
            }
            clusters.append(cluster)

        '''
        centers = ap.cluster_centers_indices_
        for c, center in enumerate(centers):
            members = np.where(C == c)[0]
            print("members\n", members)
            K = cosine_similarity(X_tfidf[members], X_tfidf[center])
            member_sims = [(m, float(k)) for m, k in zip(members, K)]
            member_sims.sort(key=lambda x: x[1], reverse=True)

            cluster = {
                "articles": [],
                "summarized": False,
                "_id": c
            }

            if len([member for member, sim in member_sims if sim > .55]) >= 3:
                # print(texts[center][:75].replace("\n", " "))

                for member, sim in member_sims:
                    # print("\t{:3.3f} ".format(sim), end='')
                    # print(articles[member]["title"][:60].replace("\n", " "))
                    cluster["articles"].append((articles[member], sim))
            else:
                continue

            clusters.append(cluster)
        '''
        # print("clusters\n", clusters)



    return clusters
