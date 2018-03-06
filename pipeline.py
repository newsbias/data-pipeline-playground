import cluster
import summarize
import json
import sys


def usage():
    print('usage: {} [webhose JSON blob]'.format(sys.argv[0]))


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    with open(sys.argv[1]) as f:
        data = json.load(f)

    articles = [
        {
            "_id": i,
            "title": x['title'],
            "text_content": x['text']
        }
        for i, x in enumerate(data['posts'])
    ]

    clusters = cluster.cluster_articles(articles)
    summaries = summarize.summarize_clusters_lexrank(clusters)
    print(json.dumps(summaries))


if __name__ == '__main__':
    main()
