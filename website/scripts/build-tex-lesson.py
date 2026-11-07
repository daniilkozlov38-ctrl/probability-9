"""Compile the deliberately small, documented lesson LaTeX dialect."""
from pathlib import Path
import re,runpy
from html_nodes import Element,parse_fragment
ROOT=Path(__file__).resolve().parents[1]
Converter=runpy.run_path(str(ROOT/'scripts/import-lessons.py'))['Converter']
SLUG='problem-solving-practice'

def render(text):
    # Comments are LaTeX comments; escaped percent signs remain visible.
    text=re.sub(r'(?<!\\)%[^\n]*','',text)
    protected=re.sub(r'(?s)(?<!\\)\$\$.*?(?<!\\)\$\$|(?<!\\)\$.*?(?<!\\)\$|\\\[.*?\\\]|\\\(.*?\\\)','',text)
    allowed={'textbf','textit','emph','underline','begin','end','item','includegraphics','webtable','section','%','{','}','\\'}
    for m in re.finditer(r'\\([A-Za-z]+|.)',protected):
        if m[1] not in allowed:raise ValueError(f'Неподдерживаемая команда вне формулы: {m[0]}')
    for name in re.findall(r'\\(?:begin|end)\{([^}]+)\}',protected):
        if name not in {'definition','designation','theorem','proof','enumerate'}:raise ValueError('Неподдерживаемое окружение: '+name)
    text=re.sub(r'(?s)\\\[(.*?)\\\]',lambda m:'$$'+m[1]+'$$',text)
    text=re.sub(r'(?s)\\\((.*?)\\\)',lambda m:'$'+m[1]+'$',text)
    text=text.replace(r'\section{',r'\section*{')
    html=Converter().render(text)
    tree=parse_fragment(html)
    # The old importer's bold-heading heuristic is irrelevant in explicit solutions.
    for parent in [tree,*list(tree.walk())]:
        children=[]
        for child in parent.children:
            if isinstance(child,Element) and child.tag=='details' and child.has_class('solution') and not child.has_class('proof'):
                body=child.find(lambda n:n.has_class('solution-body'));children.extend(body.children)
            else:children.append(child)
        parent.children=children
    for number,claim in enumerate([n for n in tree.children if isinstance(n,Element) and n.has_class('theorem')],1):
        key=f'{SLUG}/theory/claim-{number}'
        claim.attrs.update({'data-claim':key,'id':f'theorem-{number}'})
        index=tree.children.index(claim)
        following=[n for n in tree.children[index+1:] if isinstance(n,Element)]
        if not following or not following[0].has_class('proof'):raise ValueError('После theorem требуется proof')
        following[0].attrs.update({'data-for':key,'data-kind':'proof'})
    return tree.render()

def compile_lesson(source):
    source=re.sub(r'(?<!\\)%[^\n]*','',source)
    sections=list(re.finditer(r'\\section\{(Теория|Задачи|Домашнее задание)\}',source))
    if [m[1] for m in sections]!=['Теория','Задачи','Домашнее задание']:raise ValueError('Нужны разделы Теория, Задачи, Домашнее задание в этом порядке')
    out={};labels=set()
    for i,m in enumerate(sections):
        key=['theory','problems','homework'][i];text=source[m.end():sections[i+1].start() if i+1<len(sections) else len(source)].strip()
        if key=='theory':
            parts=text.split(r'\previoustheory');out[key]='<div data-theory-index="all"></div>'.join(render(p) for p in parts);continue
        pattern=re.compile(r'\\begin\{task\}\s*\\label\{([^}]+)\}(.*?)\\end\{task\}\s*\\begin\{solution\}(.*?)\\end\{solution\}',re.S)
        cursor=0;pieces=[]
        for number,t in enumerate(pattern.finditer(text),1):
            if text[cursor:t.start()].strip():raise ValueError('Каждой задаче нужны task, label и следующий solution')
            label=t[1]
            if not re.fullmatch('task-'+key+r'-[a-z0-9-]+',label) or label in labels:raise ValueError('Некорректная или повторная метка: '+label)
            labels.add(label);task_key=f'{SLUG}/{key}/{label[len("task-"+key+"-"):]}'
            condition=Element('div',{'class':'problem-statement','data-task':task_key,'id':label},parse_fragment(render(r'\textbf{'+str(number)+'.} '+t[2])).children)
            # Avoid nesting the legacy importer's statement div.
            if len(condition.children)==1 and isinstance(condition.children[0],Element) and condition.children[0].has_class('problem-statement'):condition.children=condition.children[0].children
            ident='solution-'+task_key.replace('/','-')
            detail=Element('details',{'class':'solution','id':ident,'data-for':task_key,'data-kind':'task'},[Element('summary',{'aria-controls':ident+'-body'},['Показать разбор']),Element('div',{'class':'solution-body','id':ident+'-body'},parse_fragment(render(t[3])).children)])
            pieces.extend([condition.render(),detail.render()]);cursor=t.end()
        if text[cursor:].strip() or not pieces:raise ValueError('Неполный task/solution в разделе '+key)
        out[key]='\n'.join(pieces)+'\n'
    return out

def main():
    try:out=compile_lesson((ROOT/'lessons'/f'{SLUG}.tex').read_text())
    except ValueError as e:raise SystemExit(f'Ошибка в lessons/{SLUG}.tex: {e}')
    directory=ROOT/'content'/SLUG;directory.mkdir(parents=True,exist_ok=True)
    for key,html in out.items():(directory/(key+'.html')).write_text(html)

if __name__=='__main__':main()
