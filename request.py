async def do_query(session, url, query_pairs):
	async with session.get(url, params=query_pairs) as resp:
	    resp.raise_for_status()
	    return await resp.json()
