def gen_parser(selector):
    def parse(d):
        elts = d(selector).remove('script')
        if len(elts) != 1:
            return None
        return elts.text()
    return parse


PARSERS = {
    'abc-news': gen_parser('div.article-copy'),
    'bbc-news': gen_parser('div.story-body__inner'),
    'cnbc': gen_parser('div#article_body'),
    'cnn': gen_parser('section#body-text'),
    'fox-news': gen_parser('div.article-body'),
    # TODO
    # financial-times
    # google-news
    # nbc-news
    # msnbc
    # reuters
    # politico
    # the-economist
    # time
    # the-washington-post
    # the-wall-street-journal
    # the-new-york-times
    # usa-today
    # vice-news
}
