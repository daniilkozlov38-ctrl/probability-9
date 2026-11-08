"""Small strict LaTeX-content renderer. No HTML or Python content sources."""
import re
from html_nodes import Element

class Renderer:
    def __init__(self,text):
        self.text=re.sub(r'(?<!\\)%[^\n]*','',text);self.i=0
    def space(self):
        while self.i<len(self.text) and self.text[self.i].isspace():self.i+=1
    def group(self):
        self.space()
        if self.i>=len(self.text) or self.text[self.i]!='{':raise ValueError('Ожидается {...}')
        start=self.i+1;self.i+=1;depth=1
        while self.i<len(self.text):
            c=self.text[self.i]
            if c=='\\':self.i+=2;continue
            if c=='{':depth+=1
            if c=='}':
                depth-=1
                if not depth:
                    result=self.text[start:self.i];self.i+=1;return result
            self.i+=1
        raise ValueError('Незакрытая фигурная скобка')
    def content(self,name):
        start=self.i;depth=1
        for m in re.finditer(r'\\(begin|end)\{'+re.escape(name)+r'\}',self.text[start:]):
            depth+=1 if m[1]=='begin' else -1
            if depth==0:
                end=start+m.start();self.i=start+m.end();return self.text[start:end]
        raise ValueError('Не закрыто окружение '+name)
    def parse(self):
        out=[];inline=[]
        def flush():
            nonlocal inline
            if any(not isinstance(n,str) or n.strip() for n in inline):out.append(Element('p',children=inline))
            inline=[]
        def block(n):flush();out.append(n)
        while self.i<len(self.text):
            remaining=self.text[self.i:]
            if remaining.startswith(('$$',r'\[')):
                opening=remaining[:2];closing='$$' if opening=='$$' else r'\]';end=self.text.find(closing,self.i+2)
                if end<0:raise ValueError('Не закрыта формула '+opening)
                block(Element('div',{'class':'math-display'},[r'\['+self.text[self.i+2:end].strip()+r'\]']));self.i=end+2;continue
            if remaining.startswith(('$',r'\(')):
                opening='$' if remaining[0]=='$' else r'\(';closing='$' if opening=='$' else r'\)';start=self.i+len(opening)
                m=re.search(r'(?<!\\)\$' if closing=='$' else re.escape(closing),self.text[start:])
                if not m:raise ValueError('Не закрыта формула '+opening)
                end=start+m.start();inline.append(Element('span',{'class':'math-inline'},[r'\('+self.text[start:end].strip()+r'\)']));self.i=end+len(closing);continue
            if remaining.startswith('\\'):
                m=re.match(r'\\([A-Za-z]+|.)',remaining,re.S);cmd=m[1];self.i+=m.end()
                if cmd in '%&#_{}':inline.append(cmd);continue
                if cmd=='\\':inline.append(Element('br'));continue
                if cmd=='textbackslash':self.group();inline.append('\\');continue
                if cmd in ('textbf','textit','emph','underline'):
                    inner=Renderer(self.group()).parse();children=[]
                    for n in inner:children.extend(n.children if n.tag=='p' else [n])
                    inline.append(Element({'textbf':'strong','textit':'em','emph':'em','underline':'u'}[cmd],children=children));continue
                if cmd=='href':
                    url=self.group();title=self.group()
                    if url.lower().startswith(('javascript:','data:')):raise ValueError('Недопустимая ссылка')
                    inline.append(Element('a',{'href':url},Renderer(title).inline_nodes()));continue
                if cmd=='subsection':block(Element('h3',children=Renderer(self.group()).inline_nodes()));continue
                if cmd=='interactive':
                    name=self.group()
                    if name!='conditional-geometry':raise ValueError('Неизвестная интерактивная модель: '+name)
                    block(Element('div',{'data-interactive':name}));continue
                if cmd=='previoustheory':block(Element('div',{'data-theory-index':'all'}));continue
                if cmd=='figure':
                    filename,alt,width,height=[self.group() for _ in range(4)]
                    if not re.fullmatch(r'[a-zA-Z0-9_.-]+',filename):raise ValueError('Некорректное имя рисунка')
                    alt=''.join(n if isinstance(n,str) else n.text() for n in Renderer(alt).inline_nodes())
                    block(Element('figure',{'class':'lesson-figure'},[Element('img',{'src':'../../assets/figures/'+filename,'alt':alt,'width':width,'height':height})]));continue
                if cmd=='begin':
                    name=self.group();key=None;label=None;caption=None;self.space()
                    if self.text[self.i:self.i+1]=='[':
                        end=self.text.find(']',self.i)
                        if end<0:raise ValueError('Не закрыт ключ [...]')
                        key=self.text[self.i+1:end];self.i=end+1;self.space()
                    if self.text.startswith(r'\label',self.i):self.i+=6;label=self.group()
                    if name=='tabledata':caption=self.group()
                    raw=self.content(name)
                    if name=='enumerate':
                        parts=re.split(r'\\item\b',raw)
                        if parts[0].strip():raise ValueError('В enumerate ожидается item')
                        block(Element('ol',{'class':'lesson-list'},[Element('li',children=Renderer(p).parse()) for p in parts[1:]]));continue
                    if name=='tabledata':
                        rows=[]
                        for rowindex,row in enumerate(re.split(r'\\\\',raw)):
                            if not row.strip():continue
                            cells=[]
                            for col,value in enumerate(re.split(r'(?<!\\)&',row)):
                                tag='th' if col==0 or rowindex%2==0 else 'td';attrs={'scope':'row' if col==0 else 'col'} if tag=='th' else {}
                                cells.append(Element(tag,attrs,Renderer(value.strip()).inline_nodes()))
                            rows.append(Element('tr',children=cells))
                        block(Element('div',{'class':'table-scroll','role':'region','tabindex':'0','aria-label':caption},[Element('table',children=[Element('caption',children=[caption]),Element('tbody',children=rows)])]));continue
                    body=Renderer(raw).parse()
                    if name in ('task','example','theorem','axioms','solution','proof','given','explanation'):
                        if not key or not label or not re.fullmatch(r'[a-zA-Z0-9/-]+',key) or not re.fullmatch(r'[a-zA-Z0-9-]+',label):raise ValueError('Нужны постоянный ключ [...] и label у '+name)
                        if name in ('task','example'):
                            attrs={'class':'exercise-statement' if name=='example' else 'problem-statement','data-task':key,'id':label}
                            if name=='example' and len(body)==1 and body[0].tag=='p':body=body[0].children
                            block(Element('p' if name=='example' else 'div',attrs,body))
                        elif name in ('theorem','axioms'):
                            attrs={'class':'lesson-box theorem'+(' axioms' if name=='axioms' else ''),'data-claim':key,'id':label}
                            if name=='axioms':attrs['data-axioms']='true'
                            block(Element('aside',attrs,body))
                        else:
                            kind='proof' if name=='proof' else 'given' if name=='given' else 'axioms' if name=='explanation' else 'task'
                            title={'proof':'Показать доказательство','given':'Показать решение для проверки','explanation':'Показать пояснение','solution':'Показать разбор'}[name]
                            block(Element('details',{'class':'solution'+(' proof' if name=='proof' else ' given-solution' if name=='given' else ''),'id':label,'data-for':key,'data-kind':kind},[Element('summary',{'aria-controls':label+'-body'},[title]),Element('div',{'class':'solution-body','id':label+'-body'},body)]))
                    elif name in ('definition','designation'):block(Element('aside',{'class':'lesson-box '+name},body))
                    else:raise ValueError('Неподдерживаемое окружение '+name)
                    continue
                raise ValueError('Неподдерживаемая команда вне формулы: \\'+cmd)
            if remaining.startswith('\n'):
                m=re.match(r'\n\s*\n',remaining)
                if m:flush();self.i+=m.end();continue
            m=re.match(r'[^\\$\n{}]+|\n',remaining)
            if not m:raise ValueError('Неэкранированная скобка: '+remaining[:40])
            inline.append(m[0].replace('\n',' '));self.i+=m.end()
        flush();return out
    def inline_nodes(self):
        out=[]
        for n in self.parse():out.extend(n.children if n.tag=='p' else [n])
        return out
