import { readFile, writeFile, mkdir, cp, rm } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const project = fileURLToPath(new URL('../', import.meta.url));
execFileSync('python3', [path.join(project, 'scripts/build-tex-lesson.py')], { stdio: 'inherit' });
execFileSync('python3', [path.join(project, 'scripts/prepare-theory-links.py')]);
const dist = path.join(project, 'dist');
const config = JSON.parse(await readFile(path.join(project, 'data/topics.json'), 'utf8'));
const theoryBlocks = JSON.parse(await readFile(path.join(project, 'data/theory-blocks.json'), 'utf8'));
const assetHash = createHash('sha256');
for (const name of ['styles.css', 'lessons.css', 'map.css', 'site.js', 'map.js', 'math-config.js', 'conditional-geometry.css', 'conditional-geometry-model.js', 'conditional-geometry.js']) assetHash.update(await readFile(path.join(project, 'assets', name)));
const assetVersion = assetHash.digest('hex').slice(0, 10);
const topics = [...config.topics].sort((a, b) => a.order - b.order);
const ids = new Set();
for (const [index, topic] of topics.entries()) {
  if (!/^[a-z][a-z0-9-]*$/.test(topic.id) || ids.has(topic.id)) throw new Error(`Invalid or duplicate topic id: ${topic.id}`);
  if (topic.order !== index + 1 || !topic.title.trim()) throw new Error(`Invalid topic order or title: ${topic.id}`);
  ids.add(topic.id);
}
const seenEdges = new Set();
for (const edge of config.edges) {
  const key = `${edge.from}/${edge.to}`;
  if (!ids.has(edge.from) || !ids.has(edge.to) || edge.from === edge.to || seenEdges.has(key)) throw new Error(`Invalid graph edge: ${key}`);
  for (const port of [edge.fromPort, edge.toPort]) if (!['left', 'right', 'top', 'bottom'].includes(port)) throw new Error(`Invalid edge port: ${key}`);
  if (edge.fromPosition !== undefined && (!Number.isFinite(edge.fromPosition) || edge.fromPosition < 0 || edge.fromPosition > 1)) throw new Error(`Invalid exit position: ${key}`);
  seenEdges.add(key);
}

const escape = value => String(value).replace(/[&<>"']/g, character => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[character]));
const svg = paths => `<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths}</svg>`;
const mapIcon = svg('<rect x="3" y="4" width="6" height="5" rx="1.5"/><rect x="15" y="15" width="6" height="5" rx="1.5"/><path d="M9 6.5h6a3 3 0 0 1 3 3V15M6 9v8.5h9"/>');
const listIcon = svg('<path d="M9 6h12M9 12h12M9 18h12M3 6h1M3 12h1M3 18h1"/>');
const fitIcon = svg('<path d="M9 3H3v6m12-6h6v6M3 15v6h6m12-6v6h-6"/>');
const arrowIcon = svg('<path d="M4 12h16m-6-6 6 6-6 6"/>');
const templates = Object.fromEntries(await Promise.all(['base', 'home', 'topic'].map(async name => [name, await readFile(path.join(project, `templates/${name}.html`), 'utf8')])));
function render(template, values) {
  const html = template.replace(/\{\{(\w+)\}\}/g, (_, key) => {
    if (!(key in values)) throw new Error(`Missing template variable: ${key}`);
    return values[key];
  });
  return template === templates.base ? html.replace(/\b(href|src)="([^"]+\.(?:css|js))"/g, '$1="$2?v=' + assetVersion + '"') : html;
}
function validateLesson(html, context) {
  if (html.includes('\\centering')) throw new Error(`Leaked TeX directive: ${context}`);
  const tasks = [...html.matchAll(/\bdata-task="([^"]+)"/g)].map(match => match[1]);
  const claims = [...html.matchAll(/\bdata-claim="([^"]+)"/g)].map(match => match[1]);
  const statements = [...html.matchAll(/\bclass="(?:problem-statement|exercise-statement)"/g)];
  const theorems = [...html.matchAll(/<aside\b[^>]*\bclass="[^"]*\btheorem\b[^"]*"/g)];
  if (statements.length !== tasks.length || theorems.length !== claims.length) throw new Error(`Invalid lesson structure: ${context}`);
  const disclosures = [...html.matchAll(/<details\b([^>]*)>/g)];
  const linked = new Set(disclosures.filter(match => !/\bdata-kind="given"/.test(match[1])).map(match => match[1].match(/\bdata-for="([^"]+)"/)?.[1]).filter(Boolean));
  for (const key of [...tasks, ...claims]) if (!linked.has(key)) throw new Error(`Missing solution/proof: ${key}`);
  for (const match of disclosures) if (/\sopen(?:\s|=|$)/.test(match[1])) throw new Error(`Solution open by default: ${context}`);
}
const shared = {
  siteTitle: escape(config.site.title), subject: escape(config.site.subject), class: escape(config.site.class),
  topicCount: String(topics.length), mapIcon, listIcon, arrowIcon, fitIcon
};
await rm(dist, { recursive: true, force: true });
await mkdir(dist, { recursive: true });
await cp(path.join(project, 'assets'), path.join(dist, 'assets'), { recursive: true });

const cards = topics.map(topic => `<li class="topic-node" style="--x:${topic.x}px;--y:${topic.y}px" data-topic="${topic.id}" data-x="${topic.x}" data-y="${topic.y}">
  <a class="topic-card" href="topics/${topic.id}/index.html"><span class="card-topline">${topic.additional ? '<span class="card-type">Дополнительная тема</span>' : `<span class="card-number">${String(topic.order).padStart(2, '0')}</span><span class="card-type">Тема</span>`}</span><h2>${escape(topic.title)}</h2><span class="card-bottomline">Открыть тему<span class="card-arrow">${arrowIcon}</span></span></a>
</li>`).join('\n');
const home = render(templates.home, { ...shared, cards, edges: escape(JSON.stringify(config.edges)) });
await writeFile(path.join(dist, 'index.html'), render(templates.base, {
  ...shared, root:'./', bodyClass:'home-page', pageTitle:shared.siteTitle,
  description:'Материалы уроков по теории вероятностей для 9 класса. Карта тем в порядке изучения.',
  mapCurrent:'aria-current="page"', pageAssets:'<link rel="stylesheet" href="./assets/map.css"><script src="./assets/map.js" defer></script>', body:home
}));

const sectionDefinitions = [ ['theory', 'Теория'], ['problems', 'Задачи'], ['homework', 'Домашнее задание'] ];
for (const [index, topic] of topics.entries()) {
  const content = {};
  const availableSections = sectionDefinitions.filter(([id]) => (id !== 'homework' || topic.hasHomework !== false) && (id !== 'problems' || topic.hasProblems !== false));
  for (const [key] of availableSections) {
    try { content[key] = await readFile(key === 'theory' ? path.join(project, '.generated/theory', `${topic.id}.html`) : path.join(project, '.generated/content', topic.id, `${key}.html`), 'utf8'); }
    catch (error) { if (error.code !== 'ENOENT') throw error; content[key] = ''; }
    content[key] = content[key].replace('<div data-interactive="conditional-geometry"></div>', await readFile(path.join(project, 'templates/conditional-geometry.html'), 'utf8'));
    validateLesson(content[key], `${topic.id}/${key}`);
    let headingIndex = 0;
    content[key] = content[key].replace(/<h3>/g, () => `<h3 id="${key}-subtopic-${++headingIndex}">`);
  }
  const sections = availableSections.map(([id, title], sectionIndex) => `<section class="lesson-section" id="${id}" aria-labelledby="${id}-title"><div class="section-heading"><span class="section-number">${String(sectionIndex + 1).padStart(2, '0')}</span><h2 id="${id}-title">${title}</h2></div>${content[id].trim() ? `<div class="section-content">${content[id]}</div>` : '<div class="empty-section"><span class="empty-line" aria-hidden="true"></span><p>Материалы ещё не добавлены</p></div>'}</section>`).join('\n');
  const sectionLinks = availableSections.map(([id,title], sectionIndex) => `<a href="#${id}"${sectionIndex === 0 ? ' aria-current="location"' : ''}>${id === 'homework' ? 'ДЗ' : title}</a>`).join('');
  const tocLinks = availableSections.map(([id, title]) => {
    const entries = [...content[id].matchAll(/<(?:div|aside|p|h3|figure)\b[^>]*\bid="((?:task-|theorem-|theory-block-|\w+-subtopic-)[^"]+)"[^>]*>([\s\S]*?)(?=<\/(?:div|aside|p|h3|figure)>)/g)].filter(match => id !== 'theory' || topic.tocTheory !== 'headings' || /^(theory-subtopic-|theorem-)/.test(match[1])).map(match => {
      const label = theoryBlocks.find(t => t.id === topic.id)?.blocks.find(block => block.id === match[1])?.label || match[2].match(/<strong>([\s\S]*?)<\/strong>/)?.[1].replace(/<[^>]*>/g, '').trim()
        || (match[1].includes('-subtopic-') ? match[2].replace(/<[^>]*>/g, '').trim() : match[1].startsWith('theorem-') ? `Теорема ${match[1].slice(8)}` : 'Упражнение');
      return `<a class="toc-item" href="#${escape(match[1])}">${escape(label.replace(/[.:]$/, ''))}</a>`;
    }).join('');
    return `<div class="toc-group"><a class="toc-section" href="#${id}">${title}</a>${entries}</div>`;
  }).join('');
  const previous = topics[index - 1];
  const next = topics[index + 1];
  const pagination = (target, direction) => target ? `<a class="pagination-link ${direction}" href="../${target.id}/index.html"><span>${direction === 'previous' ? '← Предыдущая тема' : 'Следующая тема →'}</span><strong>${escape(target.title)}</strong></a>` : '<span class="pagination-spacer" aria-hidden="true"></span>';
  const body = render(templates.topic, { ...shared, root:'../../', number:String(topic.order).padStart(2, '0'), topicLabel:topic.additional ? 'Дополнительная тема' : `Тема ${String(topic.order).padStart(2, '0')}`, topicTitle:escape(topic.title), sections, sectionLinks, tocLinks, previous:pagination(previous, 'previous'), next:pagination(next, 'next') });
  const directory = path.join(dist, 'topics', topic.id);
  await mkdir(directory, { recursive: true });
  await writeFile(path.join(directory, 'index.html'), render(templates.base, {
    ...shared, root:'../../', bodyClass:'topic-page', pageTitle:`${escape(topic.title)} — ${shared.siteTitle}`,
    description:escape(`${topic.title}. Теория, задачи и домашнее задание по материалам уроков.`), mapCurrent:'', pageAssets:'<link rel="stylesheet" href="../../assets/lessons.css"><script src="../../assets/math-config.js" defer></script><script src="../../assets/vendor/mathjax/tex-svg-full.js" defer></script>' + (content.theory.includes('data-geometry-lab') ? '<link rel="stylesheet" href="../../assets/conditional-geometry.css"><script src="../../assets/conditional-geometry-model.js" defer></script><script src="../../assets/conditional-geometry.js" defer></script>' : ''), body
  }));
}
console.log(`Built ${topics.length + 1} pages: the course map and ${topics.length} topic pages.`);
