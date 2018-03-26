DEFAULT_QUERYPARAMS = {
    'formatversion': 2,
    'format': 'json'
}


URL = 'https://en.wikipedia.org/w/api.php'


async def _get_json(session, url, query_params):
    params = query_params.copy()
    params.update(DEFAULT_QUERYPARAMS)
    async with session.get(url, params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def query_content(session, q):
    query_params = {
        'action': 'query',
        'prop': 'revisions',
        'redirects': 'true',
        'rvprop': 'content',
        'titles': q
    }
    return await _get_json(session, URL, query_params)


async def query_extract_intro_text(session, q, num_sentences=3):
    query_params = {
        'action': 'query',
        'prop': 'extracts',
        'redirects': 'true',
        'exintro': 'true',
        'exsentences': num_sentences,
        'explaintext': 'true',
        'titles': q
    }
    return await _get_json(session, URL, query_params)


async def parse(session, page):
    query_params = {
        'action': 'parse',
        'prop': 'text|images|templates',
        'pageid': page['pageid']
    }
    return await _get_json(session, URL, query_params)
