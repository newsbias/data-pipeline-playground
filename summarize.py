from datetime import datetime
import sumpy


def summarize_clusters_lexrank(clusters):
    summaries = []
    for i, cluster in enumerate(clusters):
        # articles = [a for a, sim in cluster["articles"] if sim > .55]
        texts = [a["text"] for a in cluster["articles"]]
        titles = [a["title"] for a in cluster["articles"]]

        text_summary = sumpy.lexrank(texts)
        titles_summary = sumpy.lexrank(titles)

        # import pdb
        # pdb.set_trace()
        best_title = titles_summary._df.head(1)['sent text'].tolist()
        best_sentence = text_summary._df.head(1)['sent text'].tolist()

        summary = {
            "title": best_title,
            "text": best_sentence,
        }

        summaries.append(summary)
    return summaries

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
