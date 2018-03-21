import news_parsers


def do_parse(source, title, url, tree):
    parser = news_parsers.PARSERS[source]
    processed = parser(tree)
    if processed is not None:
        return {
            'text': processed,
            'title': title,
            'url': url
        }
    return None
