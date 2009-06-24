import re
from cgi import escape
from urllib import quote, unquote

HTTP_RE = re.compile("((?:(http|file)://\S+)|(?:(mailto:\S+?@\S+?.\S+)))")

def _repl_func(match):
    if match is not None:
        url = match.groups()[0]
        link = "py:%s" %url
        return '<a href="%s">%s</a>' %(link, unquote(url))

def render_html(text):
    text = escape(text)
    return HTTP_RE.sub(_repl_func, text)
    
if __name__ == '__main__' :
    test = ''' An hyperlink http://test.fr bla a file, mailto:a@a.com'''
    print render_html(test)
    