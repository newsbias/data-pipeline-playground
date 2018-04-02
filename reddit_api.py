import aiohttp
import asyncio
import os
from aiohttp import web
import news_parsers
import wikipedia
from wikipedia import WikiPage
from fuzzywuzzy import fuzz
from lxml import etree
from pyquery import PyQuery as pq
import reddit
from term_frequency import get_most_common_words
import outlink_articles_intersection
from utils import attach_id


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


async def fetch_content(session, article):
    async with session.get(article['url']) as resp:
        if resp.status // 100 == 4:
            return None
        resp.raise_for_status()
        tree = await build_html_tree(resp)
        if article['source'] not in news_parsers.REDDIT_PARSERS:
            return None
        parser = news_parsers.REDDIT_PARSERS[article['source']]
        processed = parser(tree)
        if processed is None:
            return None
        return {
            'text': processed,
            'title': article['title'],
            'url': article['url']
        }


def query_heuristic(page_title, section):
    RESERVED = set((
        'External links',
        'References',
        'Bibliography',
        'Notes',
        'See also'
    ))
    if section in RESERVED:
        return 0
    if section == 'Stormy Daniels':
        return 2
    if section == 'Uncategorized':
        return 3
    return 1


def parse_request(request):
    try:
        query = request.query['q']
    except KeyError:
        raise web.HTTPBadRequest
    session = request.app['session']
    return query, session


# returns clusters for the query. calls intersection function.
# uses commented code below to create the clusters.
async def get_clustered_articles(session, keywords, page):
    import pdb
    pdb.set_trace()
    keywords_by_cluster = outlink_articles_intersection.intersection(
        page.outlinks_by_section.values(), keywords)
    # query reddit with the page title and keywords
    reddit_res_by_section = asyncio.as_completed(
        [attach_id(i, reddit.query(session, (page.title, keywords)))
         for i, keywords in enumerate(keywords_by_cluster)])

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
                article_fetchers.append(
                        attach_id(i, fetch_content(session, ra)))

    # create the clusters
    clusters = []
    for i, (_, line) in enumerate(zip(keywords_by_cluster, page.sections)):
        clusters.append({
            'keywords': page.sections['line'],
            'articles': []
        })

    article_fetcher_results = asyncio.as_completed(article_fetchers)
    j = 0
    for fut in article_fetcher_results:
        i, art = await fut
        if art is not None:
            art['_id'] = j
            clusters[i]['articles'].append(art)
            j += 1

    return clusters


async def search_handler(request):
    query, session = parse_request(request)

    page = await WikiPage.fetch(session, query)

    reddit_articles = await reddit.query(session, page.title,
                                         limit=100, sort='new')
    vocabulary = [article['title'] for article in reddit_articles]
    most_common_words = get_most_common_words(vocabulary)

    clusters = await get_clustered_articles(session, most_common_words, page)
    return web.json_response([c for c in clusters if len(c['articles']) > 0])


async def wikipedia_handler(request):
    query, session = parse_request(request)

    og_query = await wikipedia.query(
            session,
            list='search',
            srsearch=query)
    if len(og_query['query']['search']) < 1:
        return web.json_response({
            'found': False
        })

    data = await wikipedia.query_extract_intro_text_image(
        request.app['session'], og_query['query']['search'][0]['pageid'])
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
