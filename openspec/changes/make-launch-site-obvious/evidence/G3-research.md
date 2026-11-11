# G3 — роль стартовой точки: подпись или узнаваемая pin-форма

Исследовательский пакет, 2026-11-11. Семь новых первичных источников относительно локальных round3/G1/G2 реестров; пять реально открытых изображений из четырёх источников. Это чтение литературы и просмотр официальных/авторских примеров, не UX-эксперимент SpaceFox. Нет новых рейтингов кандидатов, человеческих rates, принятия дизайна или просмотра sealed banks.

**Практический вывод:** литературных оснований назначать победителя между «СТАРТ/LAUNCH рядом с сохранённым маркером» и «более знакомый pin» нет. Текст может прояснять роль, но расходует пространство и иногда замедляет поиск. Pin сообщает о location, однако сам по себе не гарантирует meaning «место старта»: в реально просмотренной wrist-работе такой pin обозначает distance fitness. Нужны отдельные ответы на три вопроса: **нашёл? понял роль старта? связал с полным именем места?**

От команды получены сообщения: G2 20/20 прошли авторские semantic/fullmask checks, reposition истинного camera anchor исправил прежние проблемы; fresh image/native review ещё идёт. Это переданные результаты, здесь не проверялись и не превращаются в human evidence.

## Источники и перенос

### G3-R01 — Influence mechanism of icon semantics on visual search performance: Evidence from an eye-tracking study

Tao Jin; Wenrui Wang; Jiamin He; Zhengxin Wu; Haoran Gu. Дата: 2023-01 (volume 93). [Первичный источник](https://www.sciencedirect.com/science/article/pii/S0169814122001433).

**Прочитано:** Abstract, highlights, introduction and publisher section snippets: Participants, Behavioural experiment results, Discussion, Conclusions; full paper NOT obtained.

**Источник:** Высокая семантическая знакомость помогала поиску; добавление текста не давало универсальной выгоды и в изученных раскладках могло замедлять поиск.

**Наша гипотеза / мутация:** Узнаваемость формы и полезность подписи проверять отдельно. Сохранённый G2-маркер + локализованное СТАРТ/LAUNCH против более узнаваемой pin-формы; не назначать победителя заранее.

**Граница доказательства:** Publisher preview; в видимом фрагменте behavioral sample — 20 студентов. Полные eye-tracking методы/размер второго sample не проверены. Не часы, не launch-site, не доказательство причинного эффекта в 5×2 SpaceFox.

### G3-R02 — How Do Older Adults Process Icons in Visual Search Tasks? The Combined Effects of Icon Type and Cognitive Aging

Jianfeng Wu; Dongfang Jiao; Chunfu Lu; Chengmin Li; Xiaofang Huang; Suzan Weng. Дата: 2022-04-08. [Первичный источник](https://www.mdpi.com/1660-4601/19/8/4525).

**Прочитано:** §§2.1–2.4 materials/participants/procedure; §§3.1–3.2 accuracy and response time; selected discussion.

**Источник:** В этой задаче icon+text превосходили icon-only по точности и времени поиска. Набрано 16 человек 60–66 лет, анализ 15 после исключения одного; группы CN/MCI.

**Наша гипотеза / мутация:** Явное слово может сокращать семантическое угадывание, особенно при незнакомой абстрактной форме. Добавить пространственно связанное слово роли к сохранённому ring/pin, сохранив полное имя места.

**Граница доказательства:** Медицинские иконки 3×3, desktop 17-inch, 65–70 cm, target задан текстом, показ до mouse click. Разные icon subsets в text/no-text условиях; малая специфическая выборка. Не часовое ограничение, не launch-map, не основание переносить rates.

### G3-R03 — The Influence of the Relationship Between Landmark Symbol Types, Annotations, and Colors on Search Performance in Mobile Maps Based on Eye Tracking

Hao Fang; Hongyun Guo; Zhangtong Song; Nai Yang; Rui Wang; Fen Guo. Дата: 2025-03-14. [Первичный источник](https://www.mdpi.com/2220-9964/14/3/129).

**Прочитано:** §§2.1–2.4 methods; §§3.1–3.2; §4.2; limitations and Data Availability; actual Fig.1.

**Источник:** В эксперименте n=40, 776×436 desktop maps, 24 символа: авторы сообщают преимущество функциональных INDEX в эффективности поиска; согласование цвета символа и подписи не улучшило поиск значимо.

**Наша гипотеза / мутация:** Функция места и связь с подписью важнее предположения, что одинаковый cyan автоматически объяснит роль. Явная роль старта + близкая подпись, сохраняя форму/контраст; цветовая связь — вспомогательная.

**Граница доказательства:** Не сравнение подпись/no-label: annotations есть в обеих color-ветвях. 20–30-летние, target задан категорией, не часы. Data Availability ошибочно/противоречиво заявляет «no new data» при описанном опыте: снижает проверяемость. Гендерные объяснения не переносим в дизайн.

### G3-R04 — Search Efficiency and Visual Appeal of Pictorial-Based and Typography-Based Map

Dorotea Kovačević; Klementina Možina. Дата: 2026-03-12. [Первичный источник](https://www.mdpi.com/2220-9964/15/3/119).

**Прочитано:** §§2.1–2.6; §3.1; §4 contextual explanations; actual Fig.1.

**Источник:** n=50, Croatian tourists, desktop city maps: text-only POI находили быстрее pictogram-only. Авторы НЕ тестировали icon+text.

**Наша гипотеза / мутация:** Прямой текст полезен как гипотеза семантического уточнения, но его добавление не доказано этим сравнением. Проверить локализованное слово роли без удаления полного имени места; не заменять всю карту текстом.

**Граница доказательства:** 1280×1024 monitor, 60 cm, no time limit. Два типа POI и речевое задание; шрифтовые/рамочные формы и spacing различались. Не watchface и не эффект избыточной подписи.

### G3-R05 — Micro Visualizations on a Smartwatch: Assessing Reading Performance While Walking

Fairouz Grioui; Tanja Blascheck; Lijie Yao; Petra Isenberg. Дата: 2024-07-25 (arXiv v1). [Первичный источник](https://arxiv.org/html/2407.17893v1).

**Прочитано:** §§2.1–2.7; §§3.1, 3.3; §4; actual Fig.1.

**Источник:** Две wrist-стадии n=18/24 на Fossil Gen6: движение ухудшало часть показателей чтения radial-progress; точное чтение и ответ занимали время. Fig.1 использует знакомый pin для distance walked.

**Наша гипотеза / мутация:** Pin не гарантирует launch-site semantics; конкуренцию с fitness проверять явно. Уникальная связь geo-marker ↔ полное место ↔ роль старта; не повторять тот же pin как метку другого поля.

**Граница доказательства:** Задание — выбрать максимум fitness progress и оценить процент, не marker search. До 12 s на стимул; response-time во второй стадии только по 70% видео. Визуальное использование pin не доказывает, что люди ошибались в его смысле.

### G3-R06 — Maps — Apple Human Interface Guidelines

Apple. Дата: current guide; change log last listed 2024-12-18; accessed 2026-11-11. [Первичный источник](https://developer.apple.com/design/human-interface-guidelines/maps/).

**Прочитано:** Best practices selected-element styling; Custom information; Place cards surrounding location-related cues; watchOS.

**Источник:** Apple рекомендует отличать selected element; pin с именем места указан как компактная location-related подсказка вокруг place card.

**Наша гипотеза / мутация:** Семантика может строиться связкой pin + полное имя, а не отдельным декоративным знаком. Сильная pin-форма рядом с местом/на карте с однозначной пространственной связью; роль старта остаётся вопросом проверки.

**Граница доказательства:** Гайд интерактивных Maps/place cards, не сравнительный UX опыт и не Garmin. Попытки загрузки Apple artwork дали 404: actual visual inspection Apple НЕ заявляется. 2–3 chars внутри annotation не норма для обязательных подписей SpaceFox.

### G3-R07 — Best practices for tiles — Wear OS

Google / Android Developers. Дата: 2025-05-20 (page last updated). [Первичный источник](https://developer.android.com/design/ui/wear/guides/surfaces/tiles/bestpractices).

**Прочитано:** Include only necessary elements; Hide app titles; Make actions instantly understandable; Show glanceable representations. Actual hide-title / DONTshowapptitle images.

**Источник:** Гайд допускает скрыть app title на маленьком Tile, чтобы сохранить высоту двух рядов. Реально просмотренная пара показывает Timer, тесноту рядов и потерю промежутков.

**Наша гипотеза / мутация:** Польза ещё одного слова должна оправдывать его реальную площадь; узнаваемая семантика не отменяет геометрические требования. Считать label support вместе с glyph support; отбрасывать пересечения с fitness/mission без сокращения обязательных полей.

**Граница доказательства:** Интерактивный Tile и 48dp targets, не пассивный Garmin face: размер и правило удаления заголовка не переносим. Нельзя удалять обязательные поля SpaceFox. Guide пример не user-study и не измеренная цена подписи.

## Журнал фактического визуального просмотра

Изображения скачаны только во временную папку в разрешённом /tmp scope и открыты `view_image` в исходном/доступном разрешении. PNG/JPG не помещались в репозиторий. Их SHA-256 и URL сохранены в JSON; медиа после просмотра удалены.

- **G3-V01 / G3-R03** — [Fig.1, Blue vs Black annotation maps](https://mdpi-res.com/ijgi/ijgi-14-00129/article_deploy/html/images/ijgi-14-00129-g001-550.jpg). Увидено: Две прямоугольные карты: одинаковые синие круговые значки и зелёные дороги; слева синие подписи, справа серые/чёрные; слева красная рамка вокруг одного POI. Это не label/no-label пара.
- **G3-V02 / G3-R04** — [Fig.1, pictorial vs typography POI](https://mdpi-res.com/ijgi/ijgi-15-00119/article_deploy/html/images/ijgi-15-00119-g001-550.jpg). Увидено: Слева чёрные pictograms в белых рамках; справа uppercase двухстрочные имена в рамках на том же сером basemap; красный YOU ARE HERE в центре. Pictograms+text condition отсутствует.
- **G3-V03 / G3-R05** — [Fig.1 three round watch stimuli](https://arxiv.org/html/2407.17893v1/figures/studies/3_stimuli.JPG). Увидено: Время сверху; три progress circles: зелёный calories, синий steps, жёлтый distance; красный pin стоит ВНУТРИ distance fitness circle. Красный heart/дуга снизу. Это контекстная неоднозначность формы, не наблюдение user error.
- **G3-V04 / G3-R07** — [Do: hide app title](https://developer.android.com/static/wear/images/design/tiles-bestpractices-hidetitle-updated.png). Увидено: Четыре значения таймера в 2×2, раздельные округлые контейнеры с промежутками, плюс снизу, icon сверху; нет слова Timer.
- **G3-V05 / G3-R07** — [Do not: keep title on small tile](https://developer.android.com/static/wear/images/design/tiles-bestpractices-DONTshowapptitle-updated.png). Увидено: Добавлено Timer под icon; 2×2 контейнеры и значения сжаты по вертикали, средние границы соприкасаются. Другая палитра/корпус иллюстрации: это не контролируемый опыт одной переменной.

## Как трактовать предложенные 5×2 вариантов

Сравнение ring+слово против другой pin-формы меняет две переменные: подпись и форму. Оно может выбрать целостный дизайн, но не докажет отдельную пользу слова. Для контекста сохранить прежний фактический G2 экспорт как baseline; дополнительные новые кандидаты для этого не обязательны. Для Atlas, где pin уже был, явно зафиксировать, чем новая pin-форма отличается от старой.

- Заморозить G2 camera/projection и истинную координату. Pin привязывать **кончиком**, ring — центром; изменение anchoring offset не должно незаметно двигать geographic site.
- Считать видимую площадь целиком: маркер, essential outline/halo, новое слово, его подложку/leader. Проверять в конечном 390×390 после всех масок, относительно фитнеса, миссии, времени и границы geo-window.
- Не освобождать место сокращением обязательных полных подписей, удалением страны/места или уменьшением уже принятых текстов. «Не помещается» — отрицательный исход конкретного решения.
- СТАРТ/LAUNCH — слова роли, не замена полному названию места. Выбирать язык интерфейса, не показывать два языка одновременно. Слово «СТАРТ» может означать действие: оформление кнопкой дополнительно проверять на ложную affordance.
- При проверке смысла сначала свободно спросить «Что обозначает этот знак?»; подсказка «покажи место старта» заранее сообщает требуемую роль. Записывать отдельно generic location, launch site, destination/target, current location, fitness distance, action button, decoration и unknown. Это предложенная кодировка ответов, не результаты наблюдений.

## Три фальсифицируемые гипотезы G3

### G3-T01 — Explicit launch-role label

**Предсказание:** Для сохранённой G2-геометрии ring/pin + локализованное СТАРТ или LAUNCH увеличивает долю свободных ответов «место старта ракеты» против той же G2-базы.

**Опровержение:** Ответ остаётся «географическая точка», «цель», «моя позиция» либо «кнопка запуска»; преимущества перед базой нет; подпись уменьшает чтение обязательных полей.

**Проверка:** Раздельно location detection, free semantic naming, association with full site name. Не сообщать назначение символа до ответа. Слово локализовать по UI; не добавлять СТАРТ и LAUNCH одновременно.

Статус: **предложено; результат не измерен**. Источники: G3-R01, G3-R02, G3-R04.

### G3-T02 — Familiar pin without extra role label

**Предсказание:** Более узнаваемая pin-форма при сохранении истинного tip anchor, полного имени места и контекста даст понятное geographic-location meaning с меньшей занятой площадью; launch-role meaning должен проверяться отдельно.

**Опровержение:** Pin читается как distance fitness, current position, destination, generic map/decor; полное место не связывается с ним или tip mislocalizes site.

**Проверка:** Не приравнивать «вижу pin» к «понимаю старт». Сохранить одинаковую camera/projection; support всех essential частей без clipping.

Статус: **предложено; результат не измерен**. Источники: G3-R01, G3-R03, G3-R05, G3-R06.

### G3-T03 — Semantic gain must survive space budget

**Предсказание:** Хотя бы одно семантическое решение помещается в 390px и сохраняет чтение всех обязательных полей без изменения принятой G2-географии; выигрывает только если benefit не куплен потерей другого содержания.

**Опровержение:** Label/pin support пересекает fitness/mission/clock/site, текст приходится сокращать/уменьшать либо его роль выглядит интерактивной кнопкой.

**Проверка:** Engineering: zero essential clipping/opaque overlap; exact required strings retained. Human: отдельные задания на time/4fields/mission/place/countdown, показатели не измерены. Численные margins заранее выбирает протокол проекта, не литература.

Статус: **предложено; результат не измерен**. Источники: G3-R04, G3-R05, G3-R07.

У model/image review корректные названия результата — «авторская семантическая проверка» или «оценка моделью по изображениям». У fullmask-проверки — геометрическая сохранность. Ни одно не является человеческой долей правильных ответов или временем wrist-glance. Если human test не проводился, эти поля остаются `null`.

Методическая запись ранее проверена в round4: [Scientific Agent Skills, arXiv:2609.00065](https://arxiv.org/abs/2609.00065), v2, revised 2026-09-02. Использована только дисциплина происхождения утверждений; не источник нормы UX и не включена в семь design-источников.
