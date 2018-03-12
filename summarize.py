from datetime import datetime
import sumpy


def summarize_clusters_lexrank(clusters):
    summaries = []
    for i, cluster in enumerate(clusters):
        # articles = [a for a, sim in cluster["articles"] if sim > .55]
        texts = [a["text_content"] for a in cluster["articles"]]

        summary = sumpy.lexrank(texts)
        sents = []

        print("summary ", i, ":\n", summary)
        print()
    '''
        for x, row in summary._df.head(5).iterrows():
            s = {"article_id": cluster["articles"][row["doc id"]]["_id"],
                 "sentence_id": row["sent id"],
                 "text": row["sent text"]}
            sents.append(s)

        summary_map = {"sentences": sents, "cluster_id": cluster["_id"],
                       "summary_type": "lexrank"}

        summaries.append(summary_map)
    '''

    return summaries
