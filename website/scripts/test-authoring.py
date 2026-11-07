"""Regression checks for editable LaTeX, labels, structures and failure handling."""
import json,runpy
from pathlib import Path
from latex_renderer import Renderer
ROOT=Path(__file__).resolve().parents[1]
compile_lesson=runpy.run_path(str(ROOT/'scripts/build-tex-lesson.py'))['compile_lesson']
for topic in json.loads((ROOT/'data/topics.json').read_text())['topics']:
 source=(ROOT/'lessons'/(topic['id']+'.tex')).read_text()
 original=compile_lesson(source,topic)
 edited=compile_lesson(source.replace(r'\section{Теория}',r'\section{Теория}'+'\nПроверка редактирования $x=1$.\n',1),topic)
 assert 'Проверка редактирования' in edited['theory'] and original['theory']!=edited['theory']
 assert original['problems']==edited['problems']
 for bad in [source.replace(r'\end{solution}','',1),source.replace(r'\section{Теория}',r'\section{Теория}\unknown{ошибка}',1)]:
  try:compile_lesson(bad,topic)
  except ValueError:pass
  else:raise AssertionError('Bad source accepted: '+topic['id'])
for bad in ['$x',r'\textbf{не закрыто',r'\begin{enumerate}\item один']:
 try:Renderer(bad).parse()
 except ValueError:pass
 else:raise AssertionError('Malformed LaTeX accepted')
print('Passed: edits in all 6 sources reach HTML; malformed content rejected.')
