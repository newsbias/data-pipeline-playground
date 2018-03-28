import aiohttp
import asyncio
import os
from aiohttp import web
import news_parsers
import wikipedia
from fuzzywuzzy import fuzz
from lxml import etree
from pyquery import PyQuery as pq
from reddit import reddit_query


async def init(app):
    app['session'] = aiohttp.ClientSession()


async def close(app):
    await app['session'].close()


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
        if resp.status // 100 == 4:
            return (id, None)
        resp.raise_for_status()
        tree = await build_html_tree(resp)
        if article['source'] not in news_parsers.REDDIT_PARSERS:
            return (id, None)
        parser = news_parsers.REDDIT_PARSERS[article['source']]
        processed = parser(tree)
        if processed is None:
            return (id, None)
        return (id, {
            'text': processed,
            'title': article['title'],
            'url': article['url']
        })


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


async def search_handler(request):
    try:
        query = request.query['q']
    except KeyError:
        raise web.HTTPBadRequest
    session = request.app['session']

    # submit query to wikipedia
    query_resp = await wikipedia.query(session, titles=query, redirects='true')
    if len(query_resp['query']['pages']) < 1:
        raise web.HTTPNotFound  # TODO something else is probably better

    # TODO heuristic on page names?
    page = query_resp['query']['pages'][0]
    sections_resp = await wikipedia.parse_sections(session, page)
    page_title = sections_resp['parse']['title']

    NUM_QUERIES = 10
    sects_to_query = [
        x['line'] for x in sorted(
            sections_resp['parse']['sections'],
            key=lambda x: query_heuristic(page_title, x),
            reverse=True)[:NUM_QUERIES]]

    print(sects_to_query)

    clusters = []
    for line in sects_to_query:
        clusters.append({
            'keywords': line,
            'articles': []
        })

    reddit_res_by_section = asyncio.as_completed(
        [reddit_query(session, (page_title, s), i)
         for i, s in enumerate(sects_to_query)])

    seen_titles = []
    article_fetchers = []
    for fut in reddit_res_by_section:
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
    if 'pageid' not in page:
        return web.json_response({
            'found': False
        })
    try:
        image = page['original']['source']
    except KeyError:
        try:
            image = page['thumbnail']['source']
        except KeyError:
            image = None
    return web.json_response({
        'found': True,
        'title': page.get('title', None),
        'summary': page.get('extract', None),
        'image': image
    })


@web.middleware
async def cors(request, handler):
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


app = web.Application(middlewares=[cors])
app.on_startup.append(init)
app.on_cleanup.append(close)

app.router.add_get('/search', search_handler)
app.router.add_get('/wikipedia', wikipedia_handler)

web.run_app(app, port=int(os.environ.get('PORT', '8080')))
