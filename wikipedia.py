DEFAULT_QUERYPARAMS = {
    'formatversion': 2,
    'format': 'json'
}


URL = 'https://en.wikipedia.org/w/api.php'

class WikiPage:

    def __init__(self, session, query):
        self.wiki_page = self.get_first_result(session, query)
        self.outlinks_by_section = self.get_outlinks_by_section(session)


    def get_outlinks_by_section(self, session):
        response = await parse(session, page, prop='sections')

        sections = response['parse']['sections']

        # TODO: do we need to call wikipedia again?
        # TODO: Let Nathan turn this into with async
        outlinks_by_section = {section['line']: get_outlinks(section) for section in sections}

        return outlinks_by_section


async def _get_json(session, url, query_params):
    params = query_params.copy()
    params.update(DEFAULT_QUERYPARAMS)
    async with session.post(url, data=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def query(session, **params):
    params['action'] = 'query'
    return await _get_json(session, URL, params)


async def query_extract_intro_text_image(session, page_id, num_sentences=3):
    return await query(session,
                       prop='extracts|pageimages',
                       redirects='true',
                       piprop='original|thumbnail',
                       pithumbsize='100',
                       exintro='true',
                       exsentences=num_sentences,
                       explaintext='true',
                       pageids=page_id)


async def get_first_result(session, srsearch):

        response = await query(session, list='search', srsearch=srsearch)
        pages = response['query']['search']


        if not len(pages) or 'pageid' not in pages[0]:
            raise web.HTTPNotFound  # TODO something else is probably better

        # submit query to wikipedia
        first_page = pages[0]
        first_page_page_id = first_page['pageid']
        
        return await query(session, pageids=first_page_page_id)

# TODO: any other filtering goes here.
# e.g. maybe we want to divide up the words into BOW dict by length here
async def get_outlinks(session, section):

    outlinks = parse_links_in_section(session, page, section)['parse']['links']

    return [link['title'] for outlink in outlinks['parse']['links'] if ':' not in link['title']]

async def _parse_nopage(session, **params):
    params['action'] = 'parse'
    return await _get_json(session, URL, params)


async def parse(session, page, **params):
    return await _parse_nopage(session, pageid=page['pageid'], **params)

async def parse_sections(session, page):
    return await parse(session, page, prop='sections')

# TODO: comment or reference the wiki api so that we understand why there's one call per section
async def parse_links_in_section(session, page, section):
    section_content = await parse(session, page, section=section['index'], prop='wikitext')['parse']['wikitext']
    section_content = section_content.replace('{{reflist}}', '')
    links = await _parse_nopage(session, text=section_content, prop='links')
    # TODO filter junk links?
    return links