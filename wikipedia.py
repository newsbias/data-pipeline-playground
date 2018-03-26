DEFAULT_QUERYPARAMS = {
    'formatversion': 2,
    'format': 'json'
}


async def _get_json(session, url, query_params):
    params = query_params.copy()
    params.update(DEFAULT_QUERYPARAMS)
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def query(session, q):
    URL = 'https://en.wikipedia.org/w/api.php'
    query_params = {
        'action': 'query',
        'prop': 'revisions',
        'redirects': 'true',
        'rvprop': 'content',
        'titles': q
    }
    return await _get_json(session, URL, query_params)


async def parse(session, page):
    URL = 'https://en.wikipedia.org/w/api.php'
    query_params = {
        'action': 'parse',
        'prop': 'text|images|templates',
        'pageid': page['pageid']
    }
    return await _get_json(session, URL, query_params)
