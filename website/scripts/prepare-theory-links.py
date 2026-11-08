"""Add stable theory permalinks and build the practice lesson's theory index."""
from pathlib import Path
import json,re
from html_nodes import Element,parse_fragment
ROOT=Path(__file__).resolve().parents[1]

def clean(text):
 text=re.sub(r'\\\(.*?\\\)|\\\[.*?\\\]','…',text,flags=re.S)
 return re.sub(r'\s+',' ',text).strip()

def main():
 topics=json.loads((ROOT/'data/topics.json').read_text())['topics']
 output=ROOT/'.generated/theory';output.mkdir(parents=True,exist_ok=True)
 catalog=[]
 for topic in topics:
  if topic['id']=='problem-solving-practice':continue
  root=parse_fragment((ROOT/'.generated/content'/topic['id']/'theory.html').read_text())
  blocks=[];heading=0;serial=0
  for n in root.children:
   if not isinstance(n,Element):continue
   if n.tag=='h3':
    heading+=1;n.attrs.setdefault('id',f'theory-subtopic-{heading}')
   if n.tag not in ('h3','p','aside','figure') or n.attrs.get('data-task'):continue
   serial+=1;n.attrs.setdefault('id',f'theory-block-{serial}')
   strong=n.find(lambda el:el.tag=='strong')
   label=clean(strong.text()) if strong and len(strong.text())>2 else clean(n.text())
   if n.tag=='figure':
    img=n.find(lambda el:el.tag=='img');label=img.attrs.get('alt','Иллюстрация') if img else 'Иллюстрация'
   if n.has_class('designation'):label+=' — обозначение'
   if not label:label='Формулы'
   label=label.rstrip('.: ')
   if len(label)>110:label=label[:107].rstrip()+'…'
   blocks.append({'id':n.attrs['id'],'label':label,'heading':n.tag=='h3'})
  catalog.append({'id':topic['id'],'title':topic['title'],'blocks':blocks})
  (output/(topic['id']+'.html')).write_text(root.render()+'\n')
 previous_ids={t["id"] for t in topics if t["order"] < next(t["order"] for t in topics if t["id"]=="problem-solving-practice")}
 index=[]
 for topic in catalog:
  if topic["id"] not in previous_ids:continue
  link=Element('a',{'href':f'../{topic["id"]}/index.html#theory'},['Теория'])
  index.append(Element('li',children=[topic['title']+' | ',link]).render())
 index=['<ul class="theory-reference-list">'+''.join(index)+'</ul>']
 path=ROOT/'.generated/content/problem-solving-practice/theory.html'
 if path.exists():
  html=path.read_text().replace('<div data-theory-index="all"></div>','\n'.join(index))
  (output/'problem-solving-practice.html').write_text(html)
 (ROOT/'data/theory-blocks.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
 print('Theory links:',sum(len(t['blocks']) for t in catalog),'blocks from',len(catalog),'topics')

if __name__=='__main__':main()
