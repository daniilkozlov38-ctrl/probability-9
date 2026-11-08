"""Regression checks for editable LaTeX, labels, structures and failure handling."""
import json,runpy
from pathlib import Path
from latex_renderer import Renderer
ROOT=Path(__file__).resolve().parents[1]
compile_lesson=runpy.run_path(str(ROOT/'scripts/build-tex-lesson.py'))['compile_lesson']
for topic in json.loads((ROOT/'data/topics.json').read_text())['topics']:
 if topic.get('type')=='trainer':continue
 source=(ROOT/'lessons'/(topic['id']+'.tex')).read_text()
 original=compile_lesson(source,topic)
 edited=compile_lesson(source.replace(r'\section{Теория}',r'\section{Теория}'+'\nПроверка редактирования $x=1$.\n',1),topic)
 assert 'Проверка редактирования' in edited['theory'] and original['theory']!=edited['theory']
 assert all(original[k]==edited[k] for k in original if k!='theory')
 for bad in [source.replace(next(marker for marker in [r'\end{solution}',r'\end{proof}',r'\end{definition}'] if marker in source),'',1),source.replace(r'\section{Теория}',r'\section{Теория}\unknown{ошибка}',1)]:
  try:compile_lesson(bad,topic)
  except ValueError:pass
  else:raise AssertionError('Bad source accepted: '+topic['id'])
for bad in ['$x',r'\textbf{не закрыто',r'\begin{enumerate}\item один']:
 try:Renderer(bad).parse()
 except ValueError:pass
 else:raise AssertionError('Malformed LaTeX accepted')
print('Passed: edits in all lesson sources reach HTML; malformed content rejected.')
