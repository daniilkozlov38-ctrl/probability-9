# Теория вероятностей · 9 класс

Все материалы редактируются в `lessons/*.tex`, по одному файлу на тему. [Инструкция](lessons/README.md).

Из корня проекта: `python3 website/scripts/preview.py`. Предпросмотр http://127.0.0.1:4173/ . Сохраните исходник и обновите браузер; Ctrl+C останавливает сервер. Нужны Python 3 и Node.js.

Разовая сборка: `node website/scripts/build.mjs`. Проверка: `python3 website/scripts/verify-site.py`. Проверки математических моделей исходной редакции уроков: `python3 website/scripts/verify-math.py` (при изменении условий задач эти тесты требуют отдельного пересмотра).

GitHub Actions собирает исходники из website/ и публикует website/dist. Шаблоны — templates/, оформление, изображения и MathJax — assets/, порядок тем и граф — data/topics.json. `.generated/` и `dist/` — результаты сборки, не источники уроков. scripts/latex_renderer.py содержит общий преобразователь, без текстов задач и решений.

Прежние HTML-исходники и импортёры убраны. [Как вернуться к прежней версии](ROLLBACK.md).
