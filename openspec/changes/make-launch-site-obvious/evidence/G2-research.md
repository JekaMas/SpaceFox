# G2 — контекст и пространство полного маркера

Проверено 2026-11-11. Это свежий целевой пакет после сообщённых root failures G1: **6 новых первичных источников**, включая одну полностью изученную по выбранным разделам статью и один явно ограниченный conference abstract. **3 официальных PNG действительно просмотрены.** Новые кандидаты/рейтинги и sealed banks не просматривались. Все human metrics ниже — гипотезы, не выполненные измерения.

## Входные наблюдения и граница роли

Root сообщил: у Earthrise все шесть glyph-вариантов не проходят full-glyph edge clearance возле старого anchor(368,148); Atlas часто конфликтует с областью между временем и миссией; в Control/Ticket/Relay есть здоровые случаи. Увеличение символа само по себе не устранило проблему. Указанный root receipt: `openspec/changes/make-launch-site-obvious/evidence/campaign.json.gz`. Исследователь его не открывал и не выставлял verdict кандидатам.

## Переносимый вывод

**Сохранять конкретный G1 glyph и менять географию/её окно независимо.** Для начала освободить полному символу место внутри круглого экрана и вне непрозрачных clock/mission/field blocks; затем менять масштаб и текстуру карты. Истинные координаты должны проецироваться в выбранный свободный участок через ту же модель карты. Нельзя просто прижать marker к краю или перенести его независимо от географии. Это инженерный вывод, а не результат исследовательского user study.

## Свежие первичные источники

| ID / источник / дата | Прочитано и собственный результат источника | Наш перенос | Ограничение |
|---|---|---|---|
| G2-R01 [Zuo et al. — The influence of target layout and target graphic type on searching performance based on eye-tracking technology](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2023.1052488/full) — 2023-02-09 | §2 Materials/methods; §3.1 and3.2 results; §4.2–4.3 interpretation; §5 limitations. 39 students,24-inch desktop,100×100px automobile-console icons; location affected some search measures and interacted with icon style. Circular-vs-rectangular comparison was indirect. | Test relocation using each retained G1 glyph/lineage; changing the anchor zone can alter visual search, and location results need not generalize across glyph styles. | Not wrist or launch-map; unlimited search, circular block always first, young sample; do not infer top-left or any single corner is universally best. |
| G2-R02 [Xia et al. — Visualizing on the Wrist: Impact of Motion, Dial Shape and Visualization Type on Smartwatch](https://pr.ieeevis.org/year/2025/program/paper_918b3f1e-6e9b-43f0-bb8b-5bad6b3956ef.html) — 2025-11-06 conference session | Official IEEE VIS abstract; Authors repository README, study design summary. Official abstract reports N32 comparing bar/radial, round/square and sitting/walking; walking reduced estimation accuracy in their task. | Treat real wrist motion and dial shape as separate external-validity conditions; a static390px clearance gate does not establish glanceability. | Full paper not obtained; no marker-search effect, direction or pixel threshold inferred. Appendix/code were not executed and no third-party summary is used as evidence. |
| G2-R03 [Android Developers — Handle different watch shapes](https://developer.android.com/training/wearables/views/layouts) — Current official documentation; page date not established | Cropping on round screens; Use a BoxInsetLayout; Figure2 window insets. A rectangular layout can crop corner content on a round single-screen UI; BoxInsetLayout defines an interior region for child content. | Compute a safe region for full glyph support, then position geography so the real launch coordinate projects into that region. | Wear OS library behavior, not Garmin-specific padding or a demonstrated minimum margin. Do not copy15dp from sample into390px as a norm. |
| G2-R04 [Esri ArcGIS Pro — Symbol units and size](https://pro.arcgis.com/en/pro-app/3.3/help/mapping/layer-properties/units-and-symbol-size.htm) — ArcGIS Pro3.3 documentation; publication date unspecified | Consistent display size vs measurable map size; Symbol units in maps; No-reference-scale examples at1:35000 and1:5000. Locator symbols may keep a consistent display size independently of changing map scale. Reference-scale symbols instead grow/shrink with the view. | Hold the exact retained G1 marker footprint fixed while varying geographic scale/radius and camera placement in G2. | Rendering semantics, not a user study. Fixed display size does not itself ensure useful context, correct position, sufficient clearance or noticeability. |
| G2-R05 [Ordnance Survey — Generalisation](https://docs.os.uk/more-than-maps/geographic-data-visualisation/guide-to-cartography/generalisation) — Undated official guide; accessed2026-11-11 | Purpose/scale and reduced space; Elimination/simplification/exaggeration/displacement; Preserving characteristics and spatial relationships. Reduced map scale requires selective detail; simplify nonessential features while preserving defining characteristics and spatial relationships. Displacement is a distinct operation. | Simplify graticule/minor texture and nonessential geography when reserving marker space; keep coastline/country context and truthful launch anchor. | General cartographic practice, not wrist experiment. The fact that some maps displace features does not authorize silently moving SpaceFox launch coordinates. |
| G2-R06 [Mapbox GL JS — Offset the vanishing point using padding](https://docs.mapbox.com/mapbox-gl-js/example/offset-vanishing-point-with-padding/) — Current official example; page date unspecified | Explanation; Marker setLngLat center; Sidebar padding with map.easeTo. Example retains geographic marker coordinates while changing camera padding to account for floating sidebars. | Reserve visual space occupied by clock/mission/fields through camera or geo-window layout; change projection/camera instead of clamping the marker. | Pitched Mapbox example, not Garmin or proof for spherical projection. Example/runtime not executed; requires an API token and no paid API was used. |

## Что реально увидено

| Источник / визуал | Наблюдение |
|---|---|
| G2-R03 [официальный PNG](https://developer.android.com/static/wear/images/02_uilib.png) | Gray inset square sits inside round display; Hello there text remains in interior. This is a conservative layout example, not measured margin guidance. |
| G2-R04 [официальный PNG](https://pro.arcgis.com/en/pro-app/3.3/help/mapping/layer-properties/GUID-C82EF854-5E1E-4EDC-BA86-791C8FAD48F8-web.png) | Overview map with cyan circular locator at one rendered size. |
| G2-R04 [официальный PNG](https://pro.arcgis.com/en/pro-app/3.3/help/mapping/layer-properties/GUID-A4B304D0-3533-4581-8075-B27F4322C90B-web.png) | Zoomed basemap shows larger buildings/roads but same cyan marker diameter as previous example. |

В примерах Esri карта действительно меняет масштаб, а голубой locator сохраняет rendered diameter. В Wear OS показан внутренний прямоугольник, который помещается в круг. Это визуальное подтверждение примеров документации, не UX-испытание SpaceFox. Временные файлы удалены после просмотра, SHA-256 и URL сохранены в JSON; медиа не добавлены в MIT-репозиторий.

## Геометрия для двадцати context mutations

Пусть `F = (круг экрана ∩ geo-window) − occupied UI`, а `G` — настоящий support полного glyph относительно его anchor: core, существенный контур/halo, pin tip и иные выступы. Тогда разрешены только anchors `p`, для которых `p + G ⊆ F` (эрозия `F ⊖ G`). Описывать pin/crosshair одним радиусом недостаточно, если его support асимметричен.

Для иллюстрации с идеальным кругом center(195,195),R195 у сообщённого anchor(368,148) radial clearance примерно **15.73 px**. Это только расстояние точки, **не** clearance полного маркера и не установленная причина провала. Фактическая convention pixel centers может отличаться.

На каждом lineage/context фиксировать: исходный G1 glyph/style/size; параметры geo-center, radius/scale, camera/projection; true projected anchor; полный support-mask; screen/geo-window/occupied-region clearance; локальную конкуренцию coast/grid/field background. Если меняется несколько контекстных факторов сразу, нельзя приписывать выигрыш единственной причине.

Инженерный gate: ноль обрезанных существенных пикселей; ноль вхождений в занятую непрозрачную UI-область; географический anchor соответствует единой проекции. Дополнительные 2 px margin — лишь предлагаемая настройка протокола. Географический контекст/полные подписи и четыре поля сохраняются.

## Три проверяемые гипотезы G2

| ID | Изменение/ожидание | Проверка | Критерий |
|---|---|---|---|
| G2-T01 / engineering_hypothesis | camera/geo-window placement, retained G1 glyph unchanged. A reserved free region for complete marker support can remove edge/UI collisions while maintaining true coordinate projection. | For each supplied G1 lineage and each of20context mutations, evaluate complete final support mask after all masks/layers, not anchor alone; subtract clock/mission/field opaque regions. | Zero clipped essential glyph/outline pixels, zero overlap with occupied UI, coordinate anchor agrees with same projection formula; optional2px clearance is a proposed margin, not source norm. |
| G2-T02 / human_hypothesis_not_executed | geography scale with fixed accepted G1 marker and controlled anchor region. Reduced/reframed geography with sufficient coast/country context makes launchpoint easier to locate than the same lineage original context. | Uncued1s marker localization, separate2s country/site reading, matched render/physical scale; compare within lineage. | Detection improves≥5percentage points; HH:MM and full country/site reading lose≤3points; engineering tests above pass. No claim of achieving these values without people. |
| G2-T03 / human_hypothesis_not_executed | nonessential map texture, geographic projection/anchor/glyph fixed. Lowering or eliminating competing minor texture near the target reduces search errors while retaining geographic meaning. | Compare retained coastline/land/country context with and without optional graticule/minor texture/decor; full required labels identical. | Marker errors reduce≥20%relative to baseline with time/field reading loss≤3percentage points; geographic correctness unchanged. This is an untested project criterion. |

Ни один предложенный процент не взят из этих статей. Геометрические вычисления/модельный visual review могут подтвердить support и clipping, но не человеческую заметность, скорость поиска или wrist reading. Успехи G1 сохраняют исходную границу доказательства; G2 меняет контекст и требует именно его проверки.

## От чего предостерегают источники

- Статья Zuo изучает100 px icons на 24-inch desktop, а не круглый Garmin. Layout comparison непрямое и с разным числом trials; нельзя объявить какой-либо угол универсально лучшим.
- VIS2025 напрямую относится к wrist motion/dial shape, но здесь изучен только официальный abstract и README аппарата. Нет оснований выдумывать маркерные эффекты или safe pixel margin.
- OS перечисляет displacement как отдельную картографическую операцию. Для SpaceFox скрытое displacement реального места старта не подходит: предпочтительны camera/layout и simplification поддерживающей карты.
- Mapbox padding показывает сохранение `setLngLat` при изменении camera center/padding. Платный/API runtime не запускался; пример не доказывает корректность конкретной Garmin globe projection.

Машиночитаемый пакет: [G2-source-ledger.json](G2-source-ledger.json). Первоначальные 12 источников/G1 сохранены отдельно. G3 label/pin packet будет целевым ответом на фактические G2 failures.

Методический checklist остаётся `scientific-critical-thinking`; текущая запись [Scientific Agent Skills](https://doi.org/10.48550/arXiv.2609.00065) уже перепроверена в этом round 4: Kassis, Agarwal, He, Patel & Brueckner (2026), v2 от 02.09.2026. Она не входит в 6 дизайн-источников. Репозиторий не менялся; paid services/installations не использовались.
