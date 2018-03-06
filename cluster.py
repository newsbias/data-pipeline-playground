from datetime import datetime
from nltk.corpus import stopwords
from nltk import word_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import AffinityPropagation
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
        tfidf = TfidfVectorizer(tokenizer=preprocess)

        good_articles = [article for article in articles
                         if article["text_content"].strip() != ""]

        texts = [article["text_content"] for article in good_articles]

        X_tfidf = tfidf.fit_transform(texts)

        print(X_tfidf)

        ap = AffinityPropagation(
                damping=0.95, max_iter=4000,
                convergence_iter=400, copy=True, preference=-4,
                affinity='euclidean', verbose=True)

        C = ap.fit_predict(X_tfidf)
        print(X_tfidf.shape, C.shape)
        print(C)
        centers = ap.cluster_centers_indices_
        for c, center in enumerate(centers):
            members = np.where(C == c)[0]
            K = cosine_similarity(X_tfidf[members], X_tfidf[center])
            member_sims = [(m, float(k)) for m, k in zip(members, K)]
            member_sims.sort(key=lambda x: x[1], reverse=True)

            cluster = {
                "articles": [],
                "summarized": False
            }

            if len([member for member, sim in member_sims if sim > .55]) >= 3:
                print(texts[center][:75].replace("\n", " "))

                for member, sim in member_sims:
                    print("\t{:3.3f} ".format(sim), end='')
                    print(good_articles[member]["title"][:60].replace(
                        "\n", " "))
                    cluster["articles"].append(
                            (good_articles[member], sim))
            else:
                continue

            cluster["_id"] = i
            i += 1
            clusters.append(cluster)

    return clusters
