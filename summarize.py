from datetime import datetime
import sumpy


def summarize_clusters_lexrank(clusters):
    summaries = []
    for cluster in clusters:
        articles = [a for a, sim in cluster["articles"] if sim > .55]
        art_texts = [a["text_content"].replace(u"\u201D", u"\"").replace(
            u"\u201C", u"\"") for a in articles]

        summary = sumpy.lexrank(art_texts)
        sents = []

        for x, row in summary._df.head(5).iterrows():
            s = {"article_id": articles[row["doc id"]]["_id"],
                 "sentence_id": row["sent id"],
                 "text": row["sent text"]}
            sents.append(s)

        summary_map = {"sentences": sents, "cluster_id": cluster["_id"],
                       "summary_type": "lexrank"}

        summaries.append(summary_map)

    return summaries
