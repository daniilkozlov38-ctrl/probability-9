"""Validate/install a handoff bundle. Never modify graph/registry or publish."""
from pathlib import Path
import argparse,json,re,runpy,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
compile_lesson=runpy.run_path(str(ROOT/'scripts/build-tex-lesson.py'))['compile_lesson']

def prepare(bundle,root=ROOT):
    bundle=Path(bundle).resolve()
    def inside(path):
        if not path.resolve().is_relative_to(bundle):raise ValueError('Путь выходит за пределы комплекта: '+str(path))
        return path
    meta=json.loads(inside(bundle/'lesson.json').read_text())
    if not isinstance(meta,dict):raise ValueError('lesson.json должен быть объектом')
    required={'id','title','status','hasHomework','solutions_reviewed','forbidden_methods','placement_note','unresolved_questions','source_notes'}
    if set(meta)!=required:raise ValueError('Поля lesson.json должны совпадать с incoming/_template/lesson.json')
    slug=meta['id']
    if not isinstance(slug,str) or not re.fullmatch(r'[a-z][a-z0-9-]*',slug):raise ValueError('Некорректный id урока')
    if not isinstance(meta['title'],str) or not meta['title'].strip():raise ValueError('Нужно название урока')
    if type(meta['hasHomework']) is not bool or type(meta['solutions_reviewed']) is not bool:raise ValueError('hasHomework/solutions_reviewed должны быть true/false')
    for key in ['forbidden_methods','unresolved_questions','source_notes']:
        if not isinstance(meta[key],list) or not all(isinstance(x,str) for x in meta[key]):raise ValueError(key+' должен быть списком строк')
    if meta['placement_note'] is not None and not isinstance(meta['placement_note'],str):raise ValueError('placement_note: строка или null')
    if meta['status']!='ready' or not meta['solutions_reviewed'] or meta['unresolved_questions']:raise ValueError('Комплект ещё не готов: нужны ready, проверенные решения и отсутствие нерешённых вопросов')
    topics=json.loads((root/'data/topics.json').read_text())['topics']
    if any(t['id']==slug for t in topics) or (root/'lessons'/(slug+'.tex')).exists():raise ValueError('Урок уже существует; для исправлений редактируйте его исходник')
    source=inside(bundle/'lesson.tex').read_text()
    sections=compile_lesson(source,meta)
    from html_nodes import parse_fragment
    images=[];figures=bundle/'figures'
    if figures.exists():
        for image in figures.iterdir():
            inside(image)
            if not image.is_file() or not re.fullmatch(r'[a-zA-Z0-9_.-]+\.(png|jpg|jpeg|svg|webp)',image.name):raise ValueError('Некорректный файл рисунка: '+image.name)
            if (root/'assets/figures'/image.name).exists():raise ValueError('Имя рисунка уже занято: '+image.name)
            images.append(image)
    supplied={p.name for p in images};used=set()
    for html in sections.values():
        for n in parse_fragment(html).walk():
            if n.tag=='img':
                name=Path(n.attrs['src']).name;used.add(name)
                if name not in supplied and not (root/'assets/figures'/name).is_file():raise ValueError('Не найден рисунок '+name)
    if supplied-used:raise ValueError('Неиспользуемые рисунки: '+', '.join(sorted(supplied-used)))
    return meta,source,images

def install(bundle,root=ROOT):
    meta,source,images=prepare(bundle,root);created=[]
    try:
        path=root/'lessons'/(meta['id']+'.tex');path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('x') as f:
            created.append(path);f.write(source)
        for image in images:
            dest=root/'assets/figures'/image.name;dest.parent.mkdir(parents=True,exist_ok=True)
            with image.open('rb') as inp,dest.open('xb') as out:
                created.append(dest);shutil.copyfileobj(inp,out)
    except Exception:
        for path in reversed(created):path.unlink(missing_ok=True)
        raise
    return meta

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('bundle',type=Path);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    try:
        meta=install(args.bundle) if args.apply else prepare(args.bundle)[0]
    except (ValueError,OSError) as e:raise SystemExit('Комплект не принят: '+str(e))
    print(('Файлы установлены: ' if args.apply else 'Комплект проверен: ')+meta['title'])
    print('Граф и реестр тем не изменены. Размещение: '+(meta['placement_note'] or 'требуется указание пользователя'))
    print('Публикация не выполнялась. Ограничения методов: '+', '.join(meta['forbidden_methods']))
if __name__=='__main__':main()
