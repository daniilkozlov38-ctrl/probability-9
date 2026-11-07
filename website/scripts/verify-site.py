"""Validate generated pages and disclosures without freezing lesson content."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from html_nodes import parse_fragment
ROOT=Path(__file__).resolve().parents[1];DIST=ROOT/'dist'
class Page(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  for key in ('href','src'):
   if key in a:self.links.append(a[key])
checked=tasks=claims=disclosures=0
for path in DIST.rglob('*.html'):
 p=Page();text=path.read_text();p.feed(text)
 assert len(p.ids)==len(set(p.ids)),path
 assert '{{' not in text and r'\centering' not in text,path
 for href in p.links:
  u=urlsplit(href)
  if u.scheme or u.netloc:continue
  target=(path.parent/unquote(u.path)).resolve() if u.path else path.resolve()
  assert target.is_relative_to(DIST.resolve()) and target.exists(),(path,href)
  if u.fragment:
   other=Page();other.feed(target.read_text());assert unquote(u.fragment) in other.ids,(path,href)
  checked+=1
 root=parse_fragment(text)
 details=[n for n in root.walk() if n.tag=='details' and n.has_class('solution')]
 assert all('open' not in n.attrs for n in details),path
 for n in root.walk():
  key=n.attrs.get('data-task') or n.attrs.get('data-claim')
  if key:
   assert any(d.attrs.get('data-for')==key and d.attrs.get('data-kind')!='given' for d in details),(path,key)
   tasks+=bool(n.attrs.get('data-task'));claims+=bool(n.attrs.get('data-claim'))
 disclosures+=len(details)
print(f'Passed: {checked} local links/anchors, {tasks} tasks, {claims} claims, {disclosures} closed disclosures.')
