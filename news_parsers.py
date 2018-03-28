def gen_parser(selector):
    def parse(d):
        if d is None:
            return None
        elts = d(selector)
        if elts is not None:
            elts = elts.remove('script')
        if elts is not None:
            elts = elts.remove('style')
        if len(elts) != 1:
            return None
        return elts.text()
    return parse


NEWSAPI_PARSERS = {
    'abc-news': gen_parser('div.article-copy'),
    'bbc-news': gen_parser('div.story-body__inner'),
    'cnbc': gen_parser('div#article_body'),
    'cnn': gen_parser('section#body-text'),
    'fox-news': gen_parser('div.article-body'),
    'nbc-news': gen_parser('div.article-body'),
    'msnbc': gen_parser('div[itemprop="articleBody"]'),
    'reuters': gen_parser('div[class^="body_"]'),
    'politico': gen_parser('div.story-text'),
    'the-economist': gen_parser('div.blog-post__text'),
    'time': gen_parser('div#article-body'),
    'the-washington-post': gen_parser('div[itemprop="articleBody"]'),
    'the-wall-street-journal': gen_parser('div.wsj-snipped-body'),
    'the-new-york-times': gen_parser('article#story'),
    'usa-today': gen_parser('article.story'),
    'vice-news': gen_parser('div.post-content'),
}

REDDIT_PARSERS = {
    'bbc': gen_parser('div.story-body__inner'),
    'cnbc': gen_parser('div#article_body'),
    'cnn': gen_parser('section#body-text'),
    'foxnews': gen_parser('div.article-body'),
    'nbcnews': gen_parser('div.article-body'),
    'msnbc': gen_parser('div[itemprop="articleBody"]'),
    'reuters': gen_parser('div[class^="body_"]'),
    'politico': gen_parser('div.story-text'),
    'economist': gen_parser('div.blog-post__text'),
    'time': gen_parser('div#article-body'),
    'washingtonpost': gen_parser('div[itemprop="articleBody"]'),
    'wsj': gen_parser('div.wsj-snipped-body'),
    'nytimes': gen_parser('article#story'),
    'usatoday': gen_parser('article.story'),
    'vice': gen_parser('div.post-content'),
}
