URL = "https://api.reddit.com/search"

DEFAULT_QUERYPARAMS = {
    'limit': 10,
    'sort': 'relevance',
    'restrict_sr': 'true',
    't': 'month',
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


async def reddit_query(session, query, i):
    subject, topic = query
    queries = [QUERY_DEFAULT, subject, topic]
    q = " AND ".join(queries)
    params = {
        'q': q
    }
    params.update(DEFAULT_QUERYPARAMS)

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

    return (i, output)
