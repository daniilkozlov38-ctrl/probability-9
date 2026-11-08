"""Test bundle installation and refusal paths in isolated temporary folders."""
from pathlib import Path
import json,runpy,tempfile,unittest
API=runpy.run_path(str(Path(__file__).with_name('add-lesson.py')))
class BundleTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);base=Path(self.tmp.name);self.root=base/'website';self.bundle=base/'bundle'
  (self.root/'data').mkdir(parents=True);(self.root/'data/topics.json').write_text('{"topics":[],"edges":[]}');self.before=(self.root/'data/topics.json').read_bytes();self.bundle.mkdir()
  self.meta=dict(id='new-topic',title='Новая тема',status='ready',hasHomework=False,solutions_reviewed=True,forbidden_methods=[],placement_note=None,unresolved_questions=[],source_notes=[])
  self.save();(self.bundle/'lesson.tex').write_text(r'''\section{Теория}
\section{Задачи}
\begin{task}[new-topic/problems/1]\label{task-problems-1}Условие $x=1$.\end{task}
\begin{solution}[new-topic/problems/1]\label{solution-new-topic-problems-1}Ответ $1$.\end{solution}''')
 def save(self):(self.bundle/'lesson.json').write_text(json.dumps(self.meta))
 def test_check_has_no_side_effects(self):
  API['prepare'](self.bundle,self.root);self.assertFalse((self.root/'lessons').exists());self.assertEqual((self.root/'data/topics.json').read_bytes(),self.before)
 def test_install_preserves_graph_and_refuses_overwrite(self):
  API['install'](self.bundle,self.root);self.assertEqual((self.root/'lessons/new-topic.tex').read_text(),(self.bundle/'lesson.tex').read_text());self.assertEqual((self.root/'data/topics.json').read_bytes(),self.before)
  with self.assertRaises(ValueError):API['install'](self.bundle,self.root)
 def test_draft_and_unresolved_rejected(self):
  self.meta['status']='draft';self.save()
  with self.assertRaises(ValueError):API['prepare'](self.bundle,self.root)
  self.meta['status']='ready';self.meta['unresolved_questions']=['Уточнить условие'];self.save()
  with self.assertRaises(ValueError):API['prepare'](self.bundle,self.root)
 def test_missing_solution_rejected(self):
  p=self.bundle/'lesson.tex';p.write_text(p.read_text().split(r'\begin{solution}')[0])
  with self.assertRaises(ValueError):API['prepare'](self.bundle,self.root)
 def test_escaping_input_symlink_rejected(self):
  (self.bundle/'lesson.tex').unlink();external=Path(self.tmp.name)/'outside.tex';external.write_text('Снаружи');(self.bundle/'lesson.tex').symlink_to(external)
  with self.assertRaises(ValueError):API['prepare'](self.bundle,self.root)
if __name__=='__main__':unittest.main()
