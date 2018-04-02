URL = "https://api.reddit.com/search"

DEFAULT_QUERYPARAMS = {
    'limit': 10,
    'sort': 'relevance',
    't': 'year',
    'type': 'link'
}

NEWS_SITES = [
    'bbc',
    'cnbc',
    'economist',
    'foxnews',
    'nbcnews',
    'nytimes',
    'msnbc',
    'reuters',
    'politico',
    'time',
    'usatoday',
    'washingtonpost',
    'wsj',
    'vice']

QUERY_DEFAULT = "(site:" + " OR site:".join(NEWS_SITES) + ')'


# TODO: move **kwargs here. That's reddit's responsibility?
async def query(session, query, **kwargs):
    if isinstance(query, str):
        subject = query
        topic = None
    else:
        subject, topic = query
    # XXX dear god this is awful
    queries = [QUERY_DEFAULT, subject]
    if topic is not None and topic != 'Uncategorized':
        queries.append(topic)
    q = " AND ".join(queries)
    params = DEFAULT_QUERYPARAMS.copy()
    params = {
        'q': q
    }
    params.update(kwargs)

    async with session.get(URL, params=params) as resp:
        resp.raise_for_status()
        obj = await resp.json()

    output = []
    for list_elt in obj['data']['children']:
        data = list_elt['data']
        title = data['title']
        url = data['url']
        # e.g. mobile.nytimes.com -> nytimes
        source_parts = data['domain'].split('.')
        source_parts.pop()  # gets rid of `com`
        source = source_parts[-1]
        output.append({
            'title': title,
            'url': url,
            'source': source
        })

    return output
