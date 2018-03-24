import aiohttp
import asyncio
import os
import sys
from aiohttp import web
import text_extract
import news_parsers
from fuzzywuzzy import fuzz
from lxml import etree
from pyquery import PyQuery as pq
import lda


URL = 'https://newsapi.org/v2/everything'


class NewsApiError(Exception):
    pass


async def init(app):
    app['session'] = aiohttp.ClientSession()


async def close(app):
    await app['session'].close()


async def newsapi_query(session, api_key, q):
    query_pairs = {
        'apikey': api_key,
        'language': 'en',
        'sortBy': 'publishedAt',
        'q': q,
        'pageSize': 100,
        'sources': ','.join(news_parsers.PARSERS.keys())
    }
    async with session.get(URL, params=query_pairs) as resp:
        resp.raise_for_status()
        data = await resp.json()
        if data['status'] != 'ok':
            raise NewsApiError
        return data['articles']


async def build_html_tree(resp):
    parser = etree.HTMLParser()
    chunk_size = 4096
    while True:
        chunk = await resp.content.read(chunk_size)
        if not chunk:
            break
        parser.feed(chunk)
    try:
        return pq(parser.close())
    except etree.XMLSyntaxError as e:
        print('syntax error: {}'.format(str(e)))
        return None


async def fetch_content(session, article):
    async with session.get(article['url']) as resp:
        try:
            resp.raise_for_status()
        except:
            return None
        tree = await build_html_tree(resp)
        if article['source']['id'] not in news_parsers.PARSERS:
            return None
        return text_extract.do_parse(
                article['source']['id'], article['title'], article['url'],
                tree)


async def handler(request):
    query = request.query['q']
    session = request.app['session']
    api_key = request.app['apikey']
    incoming = asyncio.as_completed(
            [fetch_content(session, a)
                for a in await newsapi_query(session, api_key, query)])

    seen_titles = []
    articles = []
    i = 0
    for x_fut in incoming:
        x = await x_fut
        if x is None:
            continue
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
                "url": x['url']
            }
            articles.append(article)
            i += 1

    return web.json_response(lda.do_cluster(articles))


app = web.Application()
apikey = os.environ.get('NB_NEWSAPI_API_KEY', None)
if apikey is None:
    print('API key not specified', file=sys.stderr)
    sys.exit(1)

app['apikey'] = apikey
app.on_startup.append(init)
app.on_cleanup.append(close)

app.router.add_get('/search', handler)
web.run_app(app, port=int(os.environ.get('PORT', '8080')))
