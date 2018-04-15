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


async def init(app):
    '''
    @param app aiohttp:web application
    Creates a Client Session
    '''
    app['session'] = aiohttp.ClientSession()


async def close(app):
    '''
    @param app aiohttp:web application
    Closes a Client Session
    '''
    await app['session'].close()


async def build_html_tree(resp):
    """Reads an HTML Page"""
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
    """Gets the article text"""
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


def parse_request(request):
    """Gets the Query and Session from the request"""
    try:
        query = request.query['q']
    except KeyError:
        raise web.HTTPBadRequest
    session = request.app['session']
    return query, session

async def create_cluster(session, title, topic, keywords):
    """https://stackoverflow.com/questions/33128325/how-to-set-class-attribute-with-await-in-init"""

    query = []
    query.append(topic)
    query += keywords

    cluster = Cluster(title, topic, keywords)
    await cluster._init(session, title, query)
    return cluster

class Cluster:
    """Defines object to hold a collection of articles about a given topic."""
    @classmethod
    def __init__(self, title, topic, keywords):
        """Initializes a Cluster"""
        self.title = title
        self.topic = topic
        self.keywords = keywords
        self.articles = []
        self.num_articles = 0
    
    async def _init(self, session, title, query):
        """Performs async tasks require upon construction of Cluster"""
        articles = await reddit.query(session, (title, query))
        self.articles = self.filter(articles)
        self.num_articles = len(self.articles)
    
    @classmethod
    def filter(self, articles):
        """Liechenstein similarity constant. Range from 0-100, where 0 is not similar and 100 is exact match."""
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
    
    @classmethod
    def get_json(self):
        """Prints the cluster"""
        return {"keywords": self.keywords, "topic": self.topic, "articles": [article.get_json() for article in self.articles]}

async def get_clustered_articles(session, vocabulary, page):
    """
    returns clusters for the query. calls intersection function.
    uses commented code below to create the clusters.
    """
    keywords_by_cluster = filter_keywords_by_section(page.outlinks_by_section, vocabulary)

    clusters = []
    for section in keywords_by_cluster:
        cluster = await create_cluster(session, page.title, section["topic"], section["keywords"])
        clusters.append(cluster.get_json())

    return clusters


async def search_handler(request):
    """Gets topics related to a query based on the request made"""
    query, session = parse_request(request)

    page = await WikiPage.fetch(session, query)

    reddit_articles = await reddit.query(session, page.title, limit=100, sort='new')

    vocabulary = [article.title for article in reddit_articles]

    keywords = get_keywords(vocabulary)

    clusters = await get_clustered_articles(session, keywords, page)

    return web.json_response(clusters)


async def wikipedia_handler(request):
    """Gets the main card from wikipedia"""
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
    """Enables CORS on the front-end"""
    response = await handler(request)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


app = web.Application(middlewares=[cors])
app.on_startup.append(init)
app.on_cleanup.append(close)

app.router.add_get('/search', search_handler)
app.router.add_get('/wikipedia', wikipedia_handler)

web.run_app(app, port=int(os.environ.get('PORT', '8080')))
