import asyncio
import os

import aiohttp
from aiohttp import web
from pyquery import PyQuery as pq
from fuzzywuzzy import fuzz
from lxml import etree

import news_parsers
import wikipedia
from wikipedia import WikiPage
import reddit
from utils import filter_keywords_by_section
from utils import get_keywords

'''
@param app aiohttp:web application
Creates a Client Session
'''
async def init(app):
    app['session'] = aiohttp.ClientSession()

'''
@param app aiohttp:web application
Closes a Client Session
'''
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
    async with session.get(article.url) as resp:
        if resp.status // 100 == 4:
            return None
        resp.raise_for_status()
        tree = await build_html_tree(resp)
        if article.source not in news_parsers.REDDIT_PARSERS:
            return None
        parser = news_parsers.REDDIT_PARSERS[article.source]
        processed = parser(tree)
        if processed is None:
            return None

        article.text = processed


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

class Article:
    def __init__(self, id, title, url, source):
        self.id = id
        self.title = title
        self.url = url
        self.source = source

class Cluster:
    async def __init__(self, section_id, id, articles, title, topic, keyword):
        self.articles = self.filter(articles)
        self.num_articles = len(articles)

        self.section_id = section_id
        self.id = id
        self.topic = topic
        self.keyword = keyword
    
    def filter(self, articles):
        # Liechenstein similarity constant. Range from 0-100, where 0 is not similar and 100 is exact match.
        SIMILARITY = 80
        unique_articles = []
        for article in articles:
            found_similar = False
            for unique_article in unique_articles:
                if fuzz.ratio(unique_article.title, article.title) > SIMILARITY:
                    found_similar = True
                    break
            if not found_similar:
                unique_articles.append(article)

        return unique_articles
    
    def get_json(self):
        return {"keyword": self.keyword, "topic": self.topic, "articles": self.articles}

# returns clusters for the query. calls intersection function.
# uses commented code below to create the clusters.
async def get_clustered_articles(session, keywords, page):
    keywords_by_cluster = filter_keywords_by_section(page.outlinks_by_section.values(), keywords)

    clusters = []
    for section_id, keywords in enumerate(keywords_by_cluster):
        topic = page.sections[section_id]
        for keyword_id, keyword in enumerate(keywords):
            articles = await reddit.query(session, (page.title, (topic, keyword)))
            cluster = Cluster(section_id, keyword_id, articles, page.title, topic, keyword)
            clusters.append(cluster.get_json())

    return clusters


async def search_handler(request):
    query, session = parse_request(request)

    page = await WikiPage.fetch(session, query)

    reddit_articles = await reddit.query(session, page.title, limit=100, sort='new')

    vocabulary = [article['title'] for article in reddit_articles]

    keywords = get_keywords(vocabulary)

    clusters = await get_clustered_articles(session, keywords, page)

    return web.json_response(clusters)


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
