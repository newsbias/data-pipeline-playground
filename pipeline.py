import cluster
import summarize
import json
import sys
from fuzzywuzzy import fuzz


def usage():
    print('usage: {} [webhose JSON blob]'.format(sys.argv[0]))


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    # eliminates articles with titles that have similar ordering of words in the title (high ratio that article is similar)
    seen_titles = []
    articles = []
    i = 0
    for x in data["posts"]:
        title = x['thread']['title_full']
        similar_titles = []
        for seen_title in seen_titles:
            if fuzz.ratio(title, seen_title) > 80:
                # print(title, seen_title, fuzz.ratio(title, seen_title))
                similar_titles.append(title)
        if len(similar_titles):
            pass
        else:
            seen_titles.append(title)
            article = {
                "_id": i,
                "title": title,
                "text_content": x['text'].strip(),
            }
            articles.append(article)
        i += 1
    # print(len(articles))

    clusters = cluster.cluster_articles(articles)

    import pdb
    pdb.set_trace()
    summaries = summarize.summarize_clusters_lexrank(clusters)
    # print(json.dumps(summaries))

    '''
    output_obj = []
    for summary in summaries:
        sentences = summary["sentences"]
        for sentence in sentences:
            id = sentence["article_id"]
            title = articles[id]["title"]
            text = sentence["text"]

            output_obj.append({"title": title, "summary": text})

    print(json.dumps(output_obj))
    '''


if __name__ == '__main__':
    main()
