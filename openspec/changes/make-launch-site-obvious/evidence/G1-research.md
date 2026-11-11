# G1 — маркер старта: identity, rendered size, local contrast

Дата проверки: 2026-11-11. Исследование, не оценка новых кандидатов. Пользовательский критерий: launchpoint должен быть заметен сразу; прежний провал нельзя закрыть техническим присутствием пикселя. Все обязательные данные SpaceFox и полные подписи сохраняются.

## Что установлено источниками

1. [Stachoň et al. (01.11.2018), Effect of Size, Shape and Map Background in Cartographic Visualization](https://www.mdpi.com/2220-9964/7/11/427): прочитаны методы §§5.1–5.4 и результаты §6. У 69 студентов картографии/GIS на desktop выявляли символы в 48 заданиях; большие символы и отсутствие topographic background ускоряли обнаружение. Это **не** исследование часов и **не** минимальный допустимый диаметр в пикселях.
2. [Cybulski & Ledermann (2024), The impact of point symbol similarity on visual search on maps](https://repositum.tuwien.at/handle/20.500.12708/203995): пока проверены первичная repository-запись и abstract, не полный текст. Сообщаются 33 человека и 60 карт, ухудшение поиска при большем сходстве target/distractors. Конкретный выбор формы для SpaceFox из abstract не объявляется доказанным.
3. [Li, Newman & Klasnja (23.07.2026), Exploring the Design Space of Glanceable Smartwatch Feedback Displays](https://mhealth.jmir.org/2026/1/e81972): прочитаны методы, результаты и ограничения. Финальная выборка 202 MTurk; desktop simulation, 5 с показа, задача оценки progress и запоминания времени. Stylization повышала ошибку оценки progress; significant effect salience не найден. Это не тест обнаружения map marker; результат не доказывает ни ненужность salient marker, ни пользу его увеличения.
4. [Ordnance Survey, Symbology](https://docs.os.uk/more-than-maps/geographic-data-visualisation/guide-to-cartography/symbology): прочитаны graphic variables и Points. Размер, форма, цвет и светлота создают figure-ground hierarchy; текст добавляет смысл. Официальное практическое руководство, не эксперимент на запястье.
5. [W3C, Understanding WCAG 2.2 Non-text Contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html): прочитаны SC 1.4.11, adjacent colors и Graphic Objects. Для значимой графической информации указан 3:1 к соседним цветам. Это web-критерий, не гарантия glanceability и не числовой minimum marker size.

## Наши три проверяемые гипотезы — результатов пока нет

Все численные критерии ниже **предложены для протокола**, а не взяты из публикаций. Нельзя называть модельный visual inspection пользовательским экспериментом.

| ID | Изменение | Проверка и критерий опровержения |
|---|---|---|
| G1-H1 | Меняется только rendered core diameter: 8 / 12 / 16 px. Stroke/halo фиксирован и считается отдельно. | После 1 с человек указывает launchpoint: ≥90% правильных обнаружений, ошибка координаты ≤10 px; выбранный размер должен улучшить detection к 8 px минимум на 5 п.п., без потери HH:MM более 3 п.п. Иначе гипотеза преимущества этого размера не подтверждена. |
| G1-H2 | При одном core diameter сравнить один акцентный fill и fill с чёткими light/dark контурами. | Land, ocean, coast и graticule backgrounds проверяются отдельно. Ошибок обнаружения должно стать минимум на 20% меньше, чтение HH:MM не хуже 3 п.п. Внешний bbox включает оба контура; яркий glow без чёткой кромки не считается эквивалентом. |
| G1-H3 | Уникальная для launchpoint форма и явная связь с полной подписью «Место старта» против маркера, похожего на stars/status ornaments. | После 1 с спросить «Что отмечено и где?». Ошибочных идентификаций должно стать минимум на 20% меньше; нельзя заменить обязательное место общим словом или подменить координату ради центровки. |

## До пользовательской проверки: только геометрическая/семантическая квалификация

- Считать core, stroke и halo в конечном PNG 390×390; не в увеличенном preview. Записывать минимальную видимую толщину, а не только API radius.
- Marker anchor обязан совпадать с истинной проекцией координаты. Внешний контур и вся подпись должны попадать в разрешённую область; mask/globe horizon/map viewport и круглый экран проверяются раздельно.
- Маркер рисуется последним над land, coast, graticule, trajectory и decor. «Есть в scene graph» не доказывает, что он остался видимым после всех слоёв.
- Проверить принудительные fixtures: светлая суша, тёмный океан, берег, пересечение сетки, рядом с рамкой, с длинным полным названием места. Декор не вправе иметь такую же форму/яркость, если это создаёт другой правдоподобный «старт».
- 3:1 local contrast — предварительный инженерный ориентир; при антиалиасинге, малой толщине и glare его недостаточно для UX-вывода. Полезно сравнить grayscale, но это не заменяет людей.

G2/G3 остаются условными до failure patterns после G1: исследование → гипотезы → тест → отбраковка → принятие → следующая генерация. Здесь не объявлен победитель и не принят новый макет.

## Operational scope correction before acceptance
The 1s/percentage proposals in the research packet are **future human-study ideas only**, not this run's testplan or accomplished results. The frozen executed protocol is agreed-policy.json/design.md:6actual markergrammars per family (ring24/ring28/target/pin/diamond/flag), complete source masks at3sizes, fixedhero actualJPEG pairs, and fresh model-image localization. No human-latency, causal percentage improvement or exact core8/12/16 factorial was executed.
