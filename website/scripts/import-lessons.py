"""Import the reviewed Overleaf snapshot. Run explicitly, not as part of build."""
from pathlib import Path
import html
import json
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources' / 'overleaf'
BOOK = ROOT / 'sources' / 'textbook-homework.json'


class Converter:
    def __init__(self):
        self.tokens = {}

    def token(self, value, block=False):
        key = f'ZZTOKEN{len(self.tokens)}ZZ'
        self.tokens[key] = value
        return f'\n\n{key}\n\n' if block else key

    def restore(self, text):
        for _ in range(10):
            before = text
            text = re.sub(r'ZZTOKEN\d+ZZ', lambda m: self.tokens[m[0]], text)
            if text == before:
                break
        return text

    def inline(self, text):
        # Only presentation commands are parsed here. Mathematics is protected.
        result = []
        cursor = 0
        pattern = re.compile(r'\\(textbf|textit|emph|underline)\{')
        while match := pattern.search(text, cursor):
            result.append(html.escape(text[cursor:match.start()]))
            depth, end = 1, match.end()
            start = end
            while end < len(text) and depth:
                if text[end] == '{':
                    depth += 1
                elif text[end] == '}':
                    depth -= 1
                end += 1
            if depth:
                raise ValueError('Unbalanced text command')
            tag = 'strong' if match[1] == 'textbf' else 'em' if match[1] in ('textit', 'emph') else 'u'
            result.append(f'<{tag}>{self.inline(text[start:end-1])}</{tag}>')
            cursor = end
        result.append(html.escape(text[cursor:]))
        return ''.join(result)

    def render(self, text):
        # A worked solution sometimes starts after a line break in the same
        # source paragraph. Separate it, except for the intentionally incorrect
        # solution that is itself part of an exercise's question.
        text = '\n\n'.join(
            chunk if 'Найдите ошибку' in chunk else chunk.replace(r'\textbf{Решение', '\n\n' + r'\textbf{Решение')
            for chunk in re.split(r'\n\s*\n', text)
        )
        text = re.sub(r'\\(?:begin|end)\{center\}', '', text)
        text = re.sub(r'\\centering\b', '', text)
        text = re.sub(r'\\begin\{minipage\}\{[^}]*\}|\\end\{minipage\}', '', text)
        text = text.replace(r'\newpage', '\n\n').replace(r'\hfill', '\n\n')
        math = re.compile(r'\\begin\{displaymath\}(.*?)\\end\{displaymath\}|(?<!\\)\$\$(.*?)\$\$|(?<!\\)\$(.*?)(?<!\\)\$', re.S)

        def math_replace(match):
            display = match[3] is None
            tex = next(group for group in match.groups() if group is not None).strip()
            if display:
                return self.token('<div class="math-display">\\[' + html.escape(tex) + '\\]</div>', True)
            return self.token('<span class="math-inline">\\(' + html.escape(tex) + '\\)</span>')

        text = math.sub(math_replace, text)
        env = re.compile(r'\\begin\{(definition|designation|theorem|proof|enumerate)\}(.*?)\\end\{\1\}', re.S)

        def environment(match):
            name, content = match[1], match[2]
            if name == 'enumerate':
                pieces = re.split(r'\\item\s*', content)[1:]
                value = '<ol class="lesson-list">' + ''.join('<li>' + self.render(piece) + '</li>' for piece in pieces) + '</ol>'
            elif name == 'proof':
                value = '<details class="solution proof"><summary>Показать доказательство</summary><div class="solution-body">' + self.render(content) + '</div></details>'
            else:
                value = f'<aside class="lesson-box {name}">' + self.render(content) + '</aside>'
            return self.token(value, True)

        while env.search(text):
            text = env.sub(environment, text)
        text = re.sub(r'\\section\*\{([^}]+)\}', lambda m: self.token('<h3>' + self.inline(m[1]) + '</h3>', True), text)
        figures = {
            'Противоположные события.png': ('opposite-events.png', 'Событие A и противоположное событие в пространстве исходов'),
            'вероятность противоложных событий задача 1.png': ('dice-pairs.png', 'Таблица исходов двух бросков кубика с одинаковыми результатами на диагонали'),
            'target-zones.png': ('target-zones.png', 'Рисунок 65. Мишень с десятью зонами: голубые зоны 1, 5 и 9; жёлтые зоны 4 и 8')
        }

        def figure(match):
            name, alt = figures[match[1]]
            width, height = struct.unpack('>II', (ROOT / 'assets' / 'figures' / name).read_bytes()[16:24])
            return self.token(f'<figure class="lesson-figure"><img src="../../assets/figures/{name}" alt="{alt}" width="{width}" height="{height}"></figure>', True)

        text = re.sub(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', figure, text)

        def table(match):
            data = json.loads(BOOK.read_text())['tables'][match[1]]
            rows = []
            for row_index, row in enumerate(data['rows']):
                cells = []
                for column_index, value in enumerate(row):
                    tag = 'th' if column_index == 0 or row_index % 2 == 0 else 'td'
                    scope = ' scope="row"' if column_index == 0 else ' scope="col"' if tag == 'th' else ''
                    if re.fullmatch(r'\d+/\d+', value):
                        n, d = value.split('/')
                        value = r'\(\frac{' + n + '}{' + d + r'}\)'
                    cells.append(f'<{tag}{scope}>' + html.escape(value) + f'</{tag}>')
                rows.append('<tr>' + ''.join(cells) + '</tr>')
            value = '<div class="table-scroll" role="region" tabindex="0" aria-label="' + html.escape(data['caption']) + '"><table><caption>' + html.escape(data['caption']) + '</caption><tbody>' + ''.join(rows) + '</tbody></table></div>'
            return self.token(value, True)

        text = re.sub(r'\\webtable\{([^}]+)\}', table, text)
        text = text.replace('~---', ' — ').replace('~', ' ').replace(r'\%', '%')
        text = text.replace(r'\\', self.token('<br>'))
        text = text.replace(r'\{', '{').replace(r'\}', '}')
        paragraphs = []
        for paragraph in re.split(r'\n\s*\n', text):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            if re.fullmatch(r'ZZTOKEN\d+ZZ', paragraph):
                paragraphs.append(paragraph)
                continue
            value = self.inline(re.sub(r'\s*\n\s*', ' ', paragraph))
            if re.match(r'\\textbf\{Решение', paragraph):
                paragraphs.append('<details class="solution"><summary>Показать разбор</summary><div class="solution-body"><p>' + value + '</p></div></details>')
            elif re.match(r'\\textbf\{(?:Задача\s+\d|\d+\.)', paragraph):
                paragraphs.append('<div class="problem-statement"><p>' + value + '</p></div>')
            else:
                paragraphs.append('<p>' + value + '</p>')
        value = self.restore('\n'.join(paragraphs))
        return re.sub(r'</span>([.,;:?!])', r'\1</span>', value)


def load(name):
    return (SOURCE / name).read_text()


def split_at_section(text, heading):
    expression = re.compile(r'\\begin\{center\}\s*\\section\*\{' + heading + r'\}(.*?)\\end\{center\}', re.S)
    match = expression.search(text)
    if not match:
        raise ValueError(f'Missing section {heading}')
    return text[:match.start()], match[1] + text[match.end():]


def fix(text, old, new):
    if old not in text:
        raise ValueError(f'Correction target not found: {old}')
    return text.replace(old, new)


def run():
    textbook = json.loads(BOOK.read_text()) if BOOK.exists() else {}
    lessons = {}
    t = load('2.chance_events_probability_of_elementary_events.tex')
    main, homework = split_at_section(t, 'Дз')
    theory, problems = main.split(r'\textbf{Задача 1.}', 1)
    problems = r'\textbf{Задача 1.}' + problems
    theorem = re.search(r'\\begin\{theorem\}.*?\\end\{theorem\}', problems, re.S)
    theory += '\n\n' + theorem[0]
    problems = problems[:theorem.start()] + problems[theorem.end():]
    if textbook.get('part1'):
        homework = 'Стр. 142–143.\n\n' + '\n\n'.join(r'\textbf{' + f'{i}. №{number}' + '} ' + textbook['part1'][key] for i, (key, number) in enumerate([('249g','249 (г)'),('250','250'),('257','257'),('258','258')], 1))
    lessons['random-events'] = {'theory': theory, 'problems': problems, 'homework': homework}

    t = load('3_sum_of_probabilities.tex')
    t = fix(t, 'В магазине есть чёрные, синие и белые костюмы.', 'В магазине есть чёрные, синие и белые костюмы. Костюмов каждого цвета достаточно; на обе витрины можно выставить костюмы одного цвета.')
    main, homework = split_at_section(t, 'ДЗ')
    theory, problems = split_at_section(main, 'Задачи')
    if textbook.get('part1'):
        homework = 'Первая часть учебника, стр. 143–149. В каждой задаче надо кратко перечислить все благоприятствующие элементарные события.\n\n' + '\n\n'.join(r'\textbf{' + f'{i}. №{number}' + '} ' + textbook['part1'][number] for i, number in enumerate(['272','277','282','283','285'], 1))
    lessons['addition-of-probabilities'] = {'theory': theory, 'problems': problems, 'homework': homework}

    t = load('4_equally_possible_events.tex')
    first, second = split_at_section(t, 'Вероятность противоположных событий')
    theory1, tasks1 = first.split(r'\textbf{1. [ОГЭ]}', 1)
    theory2, tasks2 = second.split(r'\textbf{Задача 5.}', 1)
    lessons['equally-likely-outcomes'] = {
        'theory': theory1 + '\n\n' + r'\section*{Вероятность противоположных событий}' + theory2,
        'problems': r'\textbf{1. [ОГЭ]}' + tasks1 + '\n\n' + r'\textbf{Задача 5.}' + tasks2
    }

    t = load('5_conditional_probability.tex')
    t = fix(t, r'k = \{1, 2,3,4,5\}', r'k \in \{1, 2,3,4,5\}')
    t = fix(t, 'Остаётся решить уравнение', 'Остаётся решить неравенство')
    t = fix(t, r'\frac{25}{26}', r'\frac{25}{36}')
    t = fix(t, r'4/6 \ 2/3', '4/6 = 2/3')
    t = fix(t, r'\mathbb{P}(B\vert A) = \frac{\mathbb{P}(A\cap B)}{\mathbb{P}(A)} = \frac{0,21}{0,3}', r'\mathbb{P}(A\vert B) = \frac{\mathbb{P}(A\cap B)}{\mathbb{P}(B)} = \frac{0,21}{0,3}')
    t = fix(t, 'Это решение верное, только, если мы достаём перчатки не все сразу, а по одной.', '')
    t = fix(t, r'Если мы хотим чтобы $\mathbb{P}(\overline{A}) \geq 0,95$, тогда это равносильно тому, что', r'Чтобы получить $\mathbb{P}(\overline{A}) \geq 0,95$, достаточно потребовать, чтобы')
    t = fix(t, 'Перебором получится, что при $n = 5$ вероятность больше $0,05$, а уже при $n = 6$ меньше.', r'При $n=4$ вероятность неудачи равна $\frac{51}{481}>0,05$, а при $n=5$ — $\frac{68}{1443}<0,05$. При меньшем числе перчаток вероятность неудачи больше. Следовательно, наименьшее подходящее количество перчаток — $n=5$.')
    main, homework = split_at_section(t, 'ДЗ')
    theory, problems = split_at_section(main, 'Задачи')
    if textbook.get('part2'):
        for label, key in [('1.} №101','101'),('2.} №103','103'),('4.} №109(г,д)','109gd')]:
            old = r'\textbf{' + label
            number = '109 (г, д)' if key == '109gd' else key
            homework = fix(homework, old, r'\textbf{' + label[:2] + f' №{number}' + '} ' + textbook['part2'][key])
    lessons['conditional-probability'] = {'theory': theory, 'problems': problems, 'homework': homework}

    t = load('6_independence.tex')
    t = fix(t, 'Найдите вероятность того, что обе батарейки окажутся исправными.', 'Найдите вероятность того, что обе батарейки окажутся исправными. Считайте исправность батареек независимой.')
    t = fix(t, 'Найдите вероятность того, что в течение года хотя бы одна лампа не перегорит.', 'Найдите вероятность того, что в течение года хотя бы одна лампа не перегорит. Считайте перегорание ламп независимым.')
    t = fix(t, r'\textit{Второе определение.} События $A$ и $B$ называются', r'\textit{Второе определение.} При $\mathbb{P}(B)>0$ события $A$ и $B$ называются')
    t = fix(t, 'Докажите, что определения эквивалентны.', r'Докажите, что определения эквивалентны при $\mathbb{P}(B)>0$.')
    main, homework = split_at_section(t, 'ДЗ')
    theory, problems = split_at_section(main, 'Задачи')
    lessons['independent-events'] = {'theory': theory, 'problems': problems, 'homework': homework}

    spelling = {'Сложение веротяностей': 'Сложение вероятностей', 'Случайаное': 'Случайное', 'событиий': 'событий', 'соответсвует': 'соответствует', 'соответсвенно': 'соответственно', 'благоприятсвующих': 'благоприятствующих', 'благопрятствующих': 'благоприятствующих', 'Привидите': 'Приведите', 'не недо учить': 'не надо учить', 'ветрину': 'витрину', 'в течении': 'в течение'}
    for topic, sections in lessons.items():
        directory = ROOT / 'content' / topic
        directory.mkdir(parents=True, exist_ok=True)
        for section, text in sections.items():
            for old, new in spelling.items():
                text = text.replace(old, new)
            value = Converter().render(text)
            (directory / f'{section}.html').write_text(value + '\n')
        print(topic, ', '.join(sections))


if __name__ == '__main__':
    run()
