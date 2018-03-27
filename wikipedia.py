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


async def query(session, **params):
    params['action'] = 'query'
    return await _get_json(session, URL, params)


async def query_extract_intro_text_image(session, q, num_sentences=3):
    return await query(session,
                       prop='extracts|pageimages',
                       redirects='true',
                       piprop='original|thumbnail',
                       pithumbsize='100',
                       exintro='true',
                       exsentences=num_sentences,
                       explaintext='true',
                       titles=q)


async def parse(session, page, **params):
    params['action'] = 'parse'
    params['pageid'] = page['pageid']
    return await _get_json(session, URL, params)


async def parse_sections(session, page):
    return await parse(session, page, prop='sections')
