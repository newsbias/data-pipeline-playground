import asyncio
from aiohttp import web
from utils import attach_id

DEFAULT_QUERYPARAMS = {
    'formatversion': 2,
    'format': 'json'
}


URL = 'https://en.wikipedia.org/w/api.php'


class WikiPage:
    # XXX you can't actually make __init__ a coroutine,
    # so we have this hack instead
    @classmethod
    async def fetch(cls, session, query):
        obj = cls()
        obj.page = await get_first_result(session, query)
        obj.title = obj.page['title']
        resp = await parse_sections(session, obj.page)
        obj.sections = resp['parse']['sections']
        obj.outlinks_by_section = await obj.get_outlinks_by_section(session)
        return obj

    async def get_outlinks_by_section(self, session):
        outlinks_by_section_fut = asyncio.as_completed(
            [attach_id(section['line'], get_outlinks(
                session, self.page, section))
             for section in self.sections])

        outlinks_by_section = {}
        for fut in outlinks_by_section_fut:
            line, outlinks = await fut
            outlinks_by_section[line] = outlinks

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

    if len(pages) == 0 or 'pageid' not in pages[0]:
        raise web.HTTPNotFound  # Signal no return value
    return pages[0]


async def get_outlinks(session, page, section):
    # TODO: any other filtering goes here.
    # e.g. maybe we want to divide up the words into BOW dict by length here
    resp = await parse_links_in_section(
        session, page, section)
    outlinks = resp['parse']['links']
    return [link['title'] for link in outlinks if ':' not in link['title']]


async def _parse_nopage(session, **params):
    params['action'] = 'parse'
    return await _get_json(session, URL, params)


async def parse(session, page, **params):
    return await _parse_nopage(session, pageid=page['pageid'], **params)


async def parse_sections(session, page):
    raw_sects = await parse(session, page, prop='sections')
    innermost_heading = {}
    for s in raw_sects['parse']['sections']:
        sect_num = int(s['number'].split('.', maxsplit=1)[0])
        sect_level = None
        if sect_num in innermost_heading:
            sect_level = innermost_heading[sect_num]['toclevel']

        if sect_level is None or s['toclevel'] > sect_level:
            innermost_heading[sect_num] = [s]
        elif s['toclevel'] == sect_level:
            innermost_heading[sect_num].append(s)

    sects = []
    for _, x in innermost_heading.items():
        sects.extend(x)
    return {
        'parse': {
            'sections': sects
        }
    }


async def parse_links_in_section(session, page, section):
    links = await parse(session, page, section=section['index'])
    return links
