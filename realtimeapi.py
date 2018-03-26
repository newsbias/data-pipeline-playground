import aiohttp
import asyncio
import os
import sys
from aiohttp import web
import text_extract
import news_parsers
import wikipedia
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


async def newsapi_fetch(session, api_key, query):
    raw_articles = await newsapi_query(session, api_key, query)

    def title_filter():
        seen_titles = []
        for ra in raw_articles:
            title = ra['title']
            found_similar = False
            for seen_title in seen_titles:
                if fuzz.ratio(title, seen_title) > 80:
                    found_similar = True
                    break
            if not found_similar:
                seen_titles.append(title)
                yield ra

    incoming = asyncio.as_completed(
            [fetch_content(session, a) for a in title_filter()])

    articles = []
    i = 0
    for x_fut in incoming:
        x = await x_fut
        if x is not None:
            x['_id'] = i
            articles.append(x)
            i += 1
    return articles


async def search_handler(request):
    try:
        query = request.query['q']
    except KeyError:
        raise web.HTTPBadRequest
    session = request.app['session']
    api_key = request.app['apikey']

    articles = await newsapi_fetch(session, api_key, query)
    return web.json_response(lda.do_cluster(articles))


async def wikipedia_handler(request):
    try:
        query_text = request.query['q']
    except KeyError:
        raise web.HTTPBadRequest

    data = await wikipedia.query_extract_intro_text_image(
            request.app['session'], query_text)
    if len(data['query']['pages']) < 1:
        return web.json_response({
            'found': False
        })
    page = data['query']['pages'][0]
    try:
        image = page['original']['source']
    except KeyError:
        try:
            image = page['thumbnail']['source']
        except KeyError:
            image = None
    return web.json_response({
        'found': True,
        'title': page['title'],
        'summary': page['extract'],
        'image': image
    })


app = web.Application()
apikey = os.environ.get('NB_NEWSAPI_API_KEY', None)
if apikey is None:
    print('API key not specified', file=sys.stderr)
    sys.exit(1)

app['apikey'] = apikey
app.on_startup.append(init)
app.on_cleanup.append(close)

app.router.add_get('/search', search_handler)
app.router.add_get('/wikipedia', wikipedia_handler)
web.run_app(app, port=int(os.environ.get('PORT', '8080')))
