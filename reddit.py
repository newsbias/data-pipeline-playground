
import request

URL = "https://api.reddit.com/search"

DEFAULT_QUERYPARAMS = {
	'limit': 10,
	'sort': 'relevance',
	'restrict_sr': 'true',
	't': 'month',
	'type': 'link'
}

NEWS_SITES = ['bbc', 'cnbc', 'economist', 'foxnews', 'nbcnews', 'nytimes', 'msnbc',
    'reuters', 'politico', 'time', 'usatoday', 'washingtonpost', 'wsj', 'vice']

QUERY_DEFAULT = "(site:" + " OR site:".join(NEWS_SITES) + ')'


async def reddit_query(session, query):
  subject, topic = query
  queries = [QUERY_DEFAULT, subject, topic]
  q = " AND ".join(queries)
  DEFAULT_QUERYPARAMS['q'] = q

  obj = await request.do_query(session, URL, DEFAULT_QUERYPARAMS)

  def process_response():
	output = []
    for list_elt in obj['data']['children']:
  	  data = list_elt['data']
  	  title = data['title']
  	  url = data['url']
  	  source = data['domain'].split('.')[1] #e.g. mobile.nytimes.com -> nytimes
	  output.append({
        'title': title,
		'url': url,
		'source': source
	  })


  return process_response(obj)
