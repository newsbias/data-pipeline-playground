import aiohttp
import asyncio
import os
import sys
import datetime
from aiohttp import web
import text_extract
import news_parsers
import wikipedia
from fuzzywuzzy import fuzz
from lxml import etree
from pyquery import PyQuery as pq


URL = 'https://newsapi.org/v2/everything'


class NewsApiError(Exception):
    pass


async def init(app):
    app['session'] = aiohttp.ClientSession()


async def close(app):
    await app['session'].close()


async def newsapi_query(session, api_key, q, id):
    today = datetime.datetime.now().date()
    two_weeks_ago = today - datetime.timedelta(weeks=2)
    query_pairs = {
        'apikey': api_key,
        'language': 'en',
        'sortBy': 'relevancy',
        'from': two_weeks_ago.isoformat(),
        'to': today.isoformat(),
        'q': q,
        'pageSize': 5,
        'sources': ','.join(news_parsers.PARSERS.keys())
    }
    async with session.get(URL, params=query_pairs) as resp:
        resp.raise_for_status()
        data = await resp.json()
        if data['status'] != 'ok':
            raise NewsApiError
        return (id, data['articles'])


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


async def fetch_content(session, article, id):
    async with session.get(article['url']) as resp:
        try:
            resp.raise_for_status()
        except:
            return None
        tree = await build_html_tree(resp)
        if article['source']['id'] not in news_parsers.PARSERS:
            return None
        return (id, text_extract.do_parse(
                article['source']['id'], article['title'], article['url'],
                tree))


def query_heuristic(page_title, section):
    RESERVED = set((
        'External links',
        'References',
        'Bibliography',
        'Notes',
        'See also'
    ))
    if section['line'] in RESERVED:
        return 0
    return 1


def construct_query(page_title, section):
    return ' '.join((
        '"{}"'.format(page_title),
        '+"{}"'.format(section['line'])))


async def search_handler(request):
    try:
        query = request.query['q']
    except KeyError:
        raise web.HTTPBadRequest
    session = request.app['session']
    api_key = request.app['apikey']

    # submit query to wikipedia
    query_resp = await wikipedia.query(session, titles=query, redirects='true')
    if len(query_resp['query']['pages']) < 1:
        raise web.HTTPNotFound  # TODO something else is probably better

    # TODO heuristic on page names?
    page = query_resp['query']['pages'][0]
    sections_resp = await wikipedia.parse_sections(session, page)
    page_title = sections_resp['parse']['title']
    sects = []
    for s in sections_resp['parse']['sections']:
        sects.append(s)

    NUM_QUERIES = 10
    sects_to_query = [
        (x['line'], construct_query(page_title, x)) for x in sorted(
            sects,
            key=lambda x: query_heuristic(page_title, x),
            reverse=True)[:NUM_QUERIES]]

    clusters = []
    for line, _ in sects_to_query:
        clusters.append({
            'keywords': line,
            'articles': []
        })

    newsapi_res_by_section = asyncio.as_completed(
            [newsapi_query(session, api_key, s, i)
             for i, (_, s) in enumerate(sects_to_query)])

    seen_titles = []
    article_fetchers = []
    for fut in newsapi_res_by_section:
        i, raw_articles = await fut
        for ra in raw_articles:
            title = ra['title']
            found_similar = False
            for seen_title in seen_titles:
                if fuzz.ratio(title, seen_title) > 80:
                    found_similar = True
                    break
            if not found_similar:
                seen_titles.append(title)
                article_fetchers.append(fetch_content(session, ra, i))

    article_fetcher_results = asyncio.as_completed(article_fetchers)
    j = 0
    for fut in article_fetcher_results:
        i, art = await fut
        if art is not None:
            art['_id'] = j
            clusters[i]['articles'].append(art)
            j += 1

    return web.json_response([c for c in clusters if len(c['articles']) > 0])


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
