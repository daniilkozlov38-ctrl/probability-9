"""Compile every lesson from its single LaTeX source. Validate before writing."""
from pathlib import Path
import json,re,shutil
from latex_renderer import Renderer
ROOT=Path(__file__).resolve().parents[1]

def compile_lesson(source,topic):
    source=re.sub(r'(?<!\\)%[^\n]*','',source)
    sections=list(re.finditer(r'\\section\{(Теория|Задачи|Домашнее задание)\}',source))
    expected=['Теория','Задачи']+([] if topic.get('hasHomework') is False else ['Домашнее задание'])
    if [m[1] for m in sections]!=expected or source[:sections[0].start()].strip():raise ValueError('Ожидаются разделы: '+', '.join(expected))
    out={};ids=set()
    for i,m in enumerate(sections):
        key=['theory','problems','homework'][i];text=source[m.end():sections[i+1].start() if i+1<len(sections) else len(source)]
        nodes=Renderer(text).parse();walk=[c for n in nodes for c in [n,*list(n.walk())]]
        for n in walk:
            ident=n.attrs.get('id')
            if ident:
                if ident in ids:raise ValueError('Повторная метка '+ident)
                ids.add(ident)
        targets=[n.attrs.get('data-task') or n.attrs.get('data-claim') for n in walk if n.attrs.get('data-task') or n.attrs.get('data-claim')]
        linked={n.attrs.get('data-for') for n in walk if n.tag=='details' and n.attrs.get('data-kind')!='given'}
        if len(set(targets))!=len(targets):raise ValueError('Повторный ключ задания или теоремы')
        for target in targets:
            if not target.startswith(topic['id']+'/'):raise ValueError('Ключ должен начинаться с '+topic['id']+'/')
            if target not in linked:raise ValueError('Нет решения/доказательства для '+target)
        out[key]='\n'.join(n.render() for n in nodes)+'\n'
    return out

def main():
    all_content={}
    for topic in json.loads((ROOT/'data/topics.json').read_text())['topics']:
        try:all_content[topic['id']]=compile_lesson((ROOT/'lessons'/(topic['id']+'.tex')).read_text(),topic)
        except ValueError as e:raise SystemExit(f'Ошибка в lessons/{topic["id"]}.tex: {e}')
    dest=ROOT/'.generated/content';temp=ROOT/'.generated/content-next'
    shutil.rmtree(temp,ignore_errors=True)
    for slug,sections in all_content.items():
        (temp/slug).mkdir(parents=True,exist_ok=True)
        for name,html in sections.items():(temp/slug/(name+'.html')).write_text(html)
    shutil.rmtree(dest,ignore_errors=True);temp.rename(dest)
if __name__=='__main__':main()
