"""Small HTML-fragment tree for the static lesson authoring pipeline."""
from html import escape
from html.parser import HTMLParser

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}


class Element:
    def __init__(self, tag, attrs=None, children=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = list(children or [])

    def has_class(self, name):
        return name in self.attrs.get('class', '').split()

    def find(self, predicate):
        return next((node for node in self.walk() if predicate(node)), None)

    def walk(self):
        for child in self.children:
            if isinstance(child, Element):
                yield child
                yield from child.walk()

    def text(self):
        return ''.join(child.text() if isinstance(child, Element) else child for child in self.children)

    def render(self):
        content = ''.join(child.render() if isinstance(child, Element) else escape(child, quote=False) for child in self.children)
        if self.tag == 'fragment':
            return content
        attrs = ''.join(' ' + key if value is None else f' {key}="{escape(str(value), quote=True)}"' for key, value in self.attrs.items())
        if self.tag in VOID:
            return f'<{self.tag}{attrs}>'
        return f'<{self.tag}{attrs}>{content}</{self.tag}>'


class FragmentParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Element('fragment')
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Element(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if len(self.stack) < 2 or self.stack[-1].tag != tag:
            raise ValueError(f'Unbalanced HTML close tag: {tag}')
        self.stack.pop()

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def parse_fragment(text):
    parser = FragmentParser()
    parser.feed(text)
    parser.close()
    if len(parser.stack) != 1:
        raise ValueError('Unclosed HTML element: ' + parser.stack[-1].tag)
    return parser.root
