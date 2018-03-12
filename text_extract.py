import readability
import lxml.html


def do_readability(text):
    doc = readability.Document(text)
    summary = doc.summary()
    body = lxml.html.document_fromstring(summary)

    return {
        'title': doc.title(),
        'text': body.text_content()
    }
