import aiohttp
import asyncio
import os
import sys
import json
from aiohttp import web
from concurrent.futures import ProcessPoolExecutor
import text_extract
from fuzzywuzzy import fuzz

import cluster
import summarize


URL = 'https://newsapi.org/v2/everything'


class NewsApiError(Exception):
    pass


def json_response(obj):
    return web.Response(text=json.dumps(obj), content_type='application/json')


async def init(app):
    app['session'] = aiohttp.ClientSession()
    app['pool'] = ProcessPoolExecutor()


async def close(app):
    await app['session'].close()
    app['pool'].shutdown()


async def newsapi_query(session, api_key, q):
    query_pairs = {
        'apikey': api_key,
        'language': 'en',
        'sortBy': 'publishedAt',
        'q': q
    }
    async with session.get(URL, params=query_pairs) as resp:
        resp.raise_for_status()
        data = await resp.json()
        if data['status'] != 'ok':
            raise NewsApiError
        return data['articles']


async def fetch_content(session, pool, article):
    async with session.get(article['url']) as resp:
        try:
            resp.raise_for_status()
        except:
            return None
        text = await resp.text()
        return await asyncio.get_event_loop().run_in_executor(
                pool, text_extract.do_readability, text)


async def handler(request):
    query = request.query['q']
    session = request.app['session']
    pool = request.app['pool']
    api_key = request.app['apikey']
    raw_articles = await asyncio.gather(
            *(fetch_content(session, pool, a)
                for a in await newsapi_query(session, api_key, query)))
    raw_articles = [x for x in raw_articles if x is not None]

    print([x['title'] for x in raw_articles])

    seen_titles = []
    articles = []
    i = 0
    for x in raw_articles:
        title = x['title']
        similar_titles = []
        for seen_title in seen_titles:
            if fuzz.ratio(title, seen_title) > 80:
                similar_titles.append(title)
        if len(similar_titles) > 0:
            pass
        else:
            seen_titles.append(title)
            article = {
                "_id": i,
                "title": x['title'],
                "text_content": x['text'],
            }
            articles.append(article)
            i += 1

    clusters = cluster.cluster_articles(articles)
    print(clusters)
    summaries = summarize.summarize_clusters_lexrank(clusters)

    output_obj = []
    for summary in summaries:
        sentences = summary['sentences']
        summary_sentences = []
        for sentence in sentences:
            text = sentence['text']
            summary_sentences.append(text)

        output_obj.append({
            'title': summary['title'],
            'summary': ' '.join(summary_sentences)
        })

    return json_response(output_obj)


app = web.Application()
apikey = os.environ.get('NB_NEWSAPI_API_KEY', None)
if apikey is None:
    print('API key not specified', file=sys.stderr)
    sys.exit(1)

app['apikey'] = apikey
app.on_startup.append(init)
app.on_cleanup.append(close)

app.router.add_get('/search', handler)
web.run_app(app)
