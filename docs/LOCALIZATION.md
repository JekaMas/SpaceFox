# Локализация SpaceFox

Добавлены **36 языков × 36 UI-строк** — полный набор идентификаторов языков
из [Connect IQ System API](https://developer.garmin.com/connect-iq/api-docs/Toybox/System.html),
проверенный 10 ноября 2026 года. Это набор ресурсов проекта; доступность каждого
языка в конкретной региональной прошивке Forerunner 165 ещё не подтверждена.
Это не обещание поддержки всех языков мира: например, отдельного кода хинди в
этом перечислении Garmin нет.

Все переводы имеют статус **draft**, `nativeQualified: false`. Проверка носителями языка остаётся отдельной необязательной оценкой. Обязательна
проверка глифов, арабского соединения букв, RTL, реальных строк конечного корпуса
и расхода памяти на Garmin для 26 основных режимов. Ни браузерная проверка, ни количество
переведённых ключей не подтверждают нативную поддержку.

## Языки

| Язык | BCP-47 / файл | Connect IQ | Направление |
| --- | --- | --- | --- |
| English | `en` | `eng` | LTR |
| Русский | `ru` | `rus` | LTR |
| Deutsch | `de` | `deu` | LTR |
| Français | `fr` | `fre` | LTR |
| Español | `es` | `spa` | LTR |
| Italiano | `it` | `ita` | LTR |
| Português | `pt` | `por` | LTR |
| Nederlands | `nl` | `dut` | LTR |
| Polski | `pl` | `pol` | LTR |
| Українська | `uk` | `ukr` | LTR |
| Čeština | `cs` | `ces` | LTR |
| Slovenčina | `sk` | `slo` | LTR |
| Magyar | `hu` | `hun` | LTR |
| Română | `ro` | `ron` | LTR |
| Български | `bg` | `bul` | LTR |
| Hrvatski | `hr` | `hrv` | LTR |
| Slovenščina | `sl` | `slv` | LTR |
| Ελληνικά | `el` | `gre` | LTR |
| Türkçe | `tr` | `tur` | LTR |
| Dansk | `da` | `dan` | LTR |
| Svenska | `sv` | `swe` | LTR |
| Norsk bokmål | `nb` | `nob` | LTR |
| Suomi | `fi` | `fin` | LTR |
| Eesti | `et` | `est` | LTR |
| Latviešu | `lv` | `lav` | LTR |
| Lietuvių | `lt` | `lit` | LTR |
| 简体中文 | `zh-Hans` | `chs` | LTR |
| 繁體中文 | `zh-Hant` | `cht` | LTR |
| 日本語 | `ja` | `jpn` | LTR |
| 한국어 | `ko` | `kor` | LTR |
| العربية | `ar` | `ara` | RTL |
| עברית | `he` | `heb` | RTL |
| Bahasa Indonesia | `id` | `ind` | LTR |
| Bahasa Melayu | `ms` | `zsm` | LTR |
| Tiếng Việt | `vi` | `vie` | LTR |
| ไทย | `th` | `tha` | LTR |

## Редактирование и проверка

`locales/catalog.json` — единственный каталог языков. Строки каждого языка находятся
в соседнем JSON-файле. Английский задаёт набор ключей и подстановок; `Body Battery`,
названия ракет, компаний и официальные названия площадок сохраняются как имена.
Названия стран сокращены для круглого экрана. Исходные значения расписания и
фитнес-полей в макете демонстрационные.

1. Исправьте нужный JSON, сохранив ключи и подстановку `{n}`.
2. Для нового кода языка обновите явный проверяемый набор кодов в
   `tools/localization.py` после сверки с актуальной документацией Garmin.
3. Выполните `python3 -B tools/build_preview.py` — он проверит ресурсы и обновит
   оба HTML-файла из `prototype/mission.template.html`, `mission.js` и `i18n.js`.
4. Откройте `prototype/index.html`, выберите язык и проверьте карту/глобус,
   три ракеты, неизвестное время, перенос и устаревание вместе.

Проверки без сторонних Python-пакетов (тестам выбора языка нужен установленный Node):

```sh
python3 -B -m unittest -v tests.test_foundation
python3 -B tools/build_preview.py --check
```

`--check` ничего не пишет и обнаруживает устаревший HTML. Исходные переводы не
заменяются английскими строками при сборке: отсутствие ключа вызывает ошибку.
В интерфейсе неизвестный язык устройства/браузера приводит к английскому.
Сохранённый поддерживаемый выбор имеет приоритет; затем проверяется список
языков браузера. Китайский различает Hans/Hant, включая регионы TW/HK/MO.

RTL применяется к тексту, а физический порядок Земля → ракета → сведения,
географические координаты, часы, числовой отсчёт и порядок фитнес-полей сохраняются.
При смене языка выбранные запуск, состояние расписания, карта и поля не сбрасываются.
Макет сохраняет настройки локально в браузере; подключения к API запусков нет.
Время берётся в Asia/Dubai для макета; нативная версия использует настройки часов.

## Нативная версия

`tools/build_native_localization.py` читает общий каталог и создаёт отдельный
JSON-словарь для каждого из 36 языков, системные строки настроек и manifest.
Коды каталога `chs`/`cht` соответствуют ресурсам Garmin `zhs`/`zht`. Генератор
сохраняет FeedBaseUrl, проекцию карты/глобуса, анимацию и все четыре поля.
Сохранённые Language=0 (English) и Language=1 (Русский) не меняют смысл;
новое значение 36 означает Auto и используется для новой установки.

`LocalePresentation` — общий владелец словаря и шрифтов активного экрана,
AOD и служебного экрана обновления. Смена языка освобождает предыдущие ресурсы
и загружает один словарь и два размера встроенного в Garmin шрифта языка
вне отрисовки. Имена моделей и компаний, часы и числовые фитнес-поля используют
общие латинские/числовые шрифты. Два общих Roboto-хэндла 22/26 px сохраняются
между сменами языка; для Roboto-языков малый хэндл используется повторно. Шрифтовые файлы SDK в репозиторий не копируются.
Семейства: RobotoRegular для латиницы, кириллицы и греческого;
NotoNaskhArabicRegular для арабского, NotoSansHebrewRegular для иврита,
NotoSansSCMedium для китайского, KosugiRegular для японского,
NanumGothicBold для корейского, PridiRegular для тайского. Массив с RobotoRegular
сам по себе не доказывает подстановку каждого отсутствующего глифа: для этого
нужны реальные наблюдения в целевом профиле.

Настройка `is24Hour` берётся из DeviceSettings; часы используют локальное время
Garmin. Дата запуска с точностью до дня остаётся гражданской датой `date_utc`
из расписания, без выдуманного точного времени или сдвига часового пояса.
Порядок даты и разделитель групп разрядов заданы явно для каждого языка в
генераторе; API отдельной пользовательской настройки этих двух форматов здесь
не заявляется. Цифры используются ASCII. Полночь/полдень в 12-часовом режиме
показываются как 12:xx. Число и единица арабского/ивритского отсчёта заключены
в Unicode LRI/PDI, сохраняя последовательность дней, часов, минут и секунд.
Текст не разворачивается по кодовым точкам. Обрезка должна сохранять графемы реально встречающихся строк конечного корпуса;
старые нормативные Unicode-векторы не являются активным приёмочным барьером.

Релизный manifest и рабочий выбор языка допускают только English и режимы
из `supportPolicy.softwareQualifiedLocales` с проверенным доказательством
конечной программной квалификации; English служит резервом. Пока проверка полноты
реального корпуса и фактических наблюдений FR165 не реализована, допуск дополнительных
языков закрыт: совпадения хешей и самоподтверждённого отчёта недостаточно.
Режим квалификации тестового приложения позволяет проверить все 36 кандидатов без
объявления их поддержанными в релизе. `nativeQualified`
не выводится из числа ресурсов или языков в профиле SDK. Технические наблюдения
FR165 Simulator API 5.2 / профиль 2502 отделены от проверки на физических
WW/APAC-часах и от проверки переводов носителями языка. Все переводы остаются
`draft`; human/native-speaker review не получен. Полный статус и незакрытые
ограничения находятся в `evidence/native-localization/whole-apply/PROGRESS.md`
основного изменения; задача 5.4 пока не закрыта.

Оригинальные переводы SpaceFox распространяются по MIT. Сторонние имена,
шрифты, география и библиотеки сохраняют собственные условия: см.
`THIRD_PARTY_NOTICES.md`.

## Основные языки: объём обязательной проверки (2026-11-13)

Политика `locales/catalog.json#supportPolicy` выбирает 26 режимов из неизменного
каталога `locales/catalog.json`: en, ru, de, fr, es, it, pt, nl, pl, uk, cs, hu, ro,
el, tr, sv, zh-Hans, zh-Hant, ja, ko, ar, he, th, id, ms, vi. Это 25 языков,
китайский в двух письменностях. bg, hr, sk, sl, da, nb, fi, et, lv, lt сохранены
как best-effort: обязательную доводку отображения для них не требуем.
Переводы, ресурсы и номера выбора всех 36 режимов сохранены.
`python3 -B tools/language_support.py` показывает недостающие обязательные
проверки отображения основных языков на реальном конечном корпусе. Проверка
носителями языка необязательна и не наблюдалась; физические часы ещё не проверены
и остаются отдельной границей приёмки продукта;
принадлежность к основным языкам сама не меняет `nativeQualified` и не даёт
допуск в manifest. Допуск требует отдельного проверенного software proof;
непроверенные human/device-флаги не блокируют этот программный допуск.
Целостность ввода/графем, обычный UI, предел 8192 байт и защита памяти/кэша
остаются обязательными. Не расширяем матрицу ради редкого Unicode и произвольных
смешанных письменностей в именах провайдера.

## Current-only format and finite text qualification — 2026-11-13

The sole public current format is `native-motion-v3`: envelope schema 3 at
`/feed.json`, with SFR1M visuals. SFR1 token/raster primitives inside SFR1M are
implementation dependencies, not a separately supported public profile. Old wire
majors, dual roots, static exporters, legacy migration/adoption, old-archive gates,
cross-version tests and the 90-day transition are RETIRED by explicit user decision,
not passed. Existing immutable evidence remains historical with its original scope.

Same-current-format accepted/pending updates, exact immutable current/recovery
closure, atomic cache activation/reopen, namespace isolation, source age, shared
quota, corruption refusal and all existing resource/time/UI bounds remain required.
A previous content generation of this same format is recoverable content, not an
old format. No schema or envelope is invented by this revision.

Display qualification uses only the finite real corpus: every launch since
2021-11-13T00:00:00Z (the last five years at this decision), ALL published future
launches paginated through `next=null`, and actual UI/menu text. Retain exact raw
page proofs, query/capture time, unique IDs/counts, completeness and verbatim strings;
a partial fetch or first future page cannot close coverage. Technical malformed,
size, interruption and integrity tests may mutate real records, without invented
display names. Do not expand display work with synthetic mixed scripts, arbitrary
Unicode or normative edgecase vectors. Grapheme/input integrity is required for
this real corpus; source-time/arithmetic/error boundaries remain technical contracts.

All 36 locale resources and selection IDs remain. The five primary modes en, ru, de, fr and es
have mandatory finite-corpus FR165 font/glyph/RTL/layout checks; the other31 are best-effort.
`tools/language_support.py` reports software observations separately from unobserved
human and physical evidence. Human translation review is not an extra five-language software
prerequisite. Physical product acceptance remains a separate existing release task.
Criterion booleans alone do not admit languages. Production selection and manifest
admission use `supportPolicy.softwareQualifiedLocales` only after validation of its
source-bound finite-corpus software proof; English remains the bootstrap fallback.
Per-row `nativeQualified`, human and physical flags stay truthful and do not control
software admission. Translations remain draft until actually reviewed.
