# Финальное ревью спецификации и жизненного цикла

Дата: 2026-11-11. Объект: четыре capability SpaceFox, текущие решения владельца,
архитектура, задачи, MIT-инструкции настройки/выпуска и фактическое дерево проекта.
Это **собственное ревью по первичным источникам**, не независимое ревью и не
приёмка нативного приложения. [Источники и границы](sources.md).

Проверенная текущая структура: **53 требования и99 сценариев** в четырёх capability.

Цель: единый непротиворечивый план от разработки до личной установки и бесплатного
Store-релиза, с отдельными каналами кода/ассетов/данных и проверяемыми failure cases.
Критерий текущего increment: четыре структурно корректные capability, устранённые
внутренние противоречия, сохранённые требования владельца, явные внешние блокеры и
публикация оригинальной MIT-ревизии с readback. Нативная готовность не является
результатом этой проверки.

## Найдено и исправлено в контракте

| ID | До ревью / следствие | Принятое исправление и владелец |
| --- | --- | --- |
| F01 | Старый design продолжал рекомендовать боковую карту, белое время и правый столбец; native выбор назывался открытым |04/full active — единственный default; старые варианты помечены историческими. Watchface/design |
| F02 | AGENT_SETUP всё ещё обещал `!` и отдельный stale-значок | Янтарный countdown + независимый пунктир; ни тучки, ни `!`. Watchface/guide |
| F03 | Полноэкранная яркая карта могла читаться как обещание AOD | Отдельная sparse AMOLED scene, minute updates, lit-pixel/burn-in и power proof. Watchface/task5.5 |
| F04 | Последняя версия SDK/API могла быть принята за поддержку устройства | Checked FR165 API 5.2, только qualified products/APIs; Music отдельно. Release/task2.2 |
| F05 | Графика могла подразумевать binary API6 или непроверенный durable bitmap | JSON-geometry qualification baseline, bitmap только после target transfer/persist/reboot proof; нет executable assets. Visual/task4.5 |
| F06 | Глобальный manifest мог расти прямо на часах | Только bounded slice manifest/dependency closure; global publisher index вне часов. Visual |
| F07 | Источник восстановления publisher — публичный CDN snapshot/cache | Durable feed-state active/pending/quota,64KiB current ledger; Git history отдельно. Schedule/task3.5 |
| F08 | Concurrency ошибочно считалась достаточной защитой порядка | Expected-base/CAS, source revision guard, monotonic generation и crash reconciliation. Schedule/task3.5 |
| F09 | Свежий deploy мог не включать «неизменившиеся» файлы | Complete Pages artifact с current/retained compatible content; pinned reconstruction после artifact expiration. Schedule/guide |
| F10 | Обновления приложения, картинок и расписания не имели отдельных правил | Signed native code versus static supported content, отдельные version axes. Release |
| F11 | Не были закреплены ключ, UUID и release provenance | Same4096-bit key/production UUID, backup вне Git/data job, source/toolchain/package digests. Release/task7.1 |
| F12 | Не был определён путь PRG→IQ→review→approved install | Личный device PRG, отдельная Store-квалификация и честный pending status; beta owner-only с другим UUID. Release/task7.3 |
| F13 | Не определены совместимость и откат | Current+previous wire major≥90days после объявления, compatible assets, higher-version code fix, new-generation asset rollback без ложной свежести. Release/task7.2 |
| F14 | Не описаны миграции и смена feed | Сохранение четырёх полей/locale/map/URL; namespace isolation. PRG→Store, beta→production и uninstall survival не обещаются без наблюдения. Release |
| F15 | Другой семье мог понадобиться author SDK/key или author feed | Official free binary + свой publisher fork/FeedBaseUrl; native fork со своей identity. Guide/release |
| F16 | Байт-предел обещал проверку «до parsing», хотя JSON мог уже распарсить Garmin | Publisher prepublication byte ceiling + native parser/shape/error qualification; callback не выдаётся за preallocation guard. Schedule/task2.2 |
| F17 | Медленные ассеты могли задержать срочный перенос запуска | Новые valid schedule факты принимаются с compatible generic/no-point fallback; предыдущую ракету нельзя переименовать в новую. Visual/task4.5 |
| F18 | Граница background/foreground и health access была расплывчатой | Deadline/resumable staging, small exit token, cached foreground; recent Garmin samples без raw sensors/GPS/upload. Watchface |
| F19 | Публикация исходников могла звучать как уже работающий продукт | README/proposal/guide явно отделяют MIT GitHub от Pages, PRG и Store. Все product tasks открыты |
| F20 | Privacy «нет отправки» могла читаться как отсутствие любых технических логов хоста | Health/identity не отправляются; обычные HTTP-запросы видит выбранный хост. Listing/privacy описывают реальную зависимость |

Изменённая часть контракта F16 сохраняет потолок8192decodedUTF-8байта; исправлена
неподтверждённая точка исполнения проверки. Схема compressed/columnar не выбрана
по desktop size study. F07 сознательно заменяет прежнее обещание «без commits»:
state checkpoint в отдельной ветке нужен для durable due/quota/reschedule; source
main и cron wakeups не заполняются heartbeat commits.

## Внешние вопросы и обязательные доказательства

| Вопрос | Текущее свидетельство | Что требуется, кто владеет |
| --- | --- | --- |
| Platform eligibility | Доступная редакция guidelines содержит under13; возраст/допустимость целевого использования не установлены | Owner clarification/current terms до native development/use, task2.3; частная установка не заявлена исключением. Личные сведения публично не сохранять |
| SensorHistory | Официальные App Types и permission table расходятся для watchface | Target compile/runtime/permission/sample proof, tasks2.2/5.5; не обещать доступность и не удалять поля молча |
| Графика, parser, storage | Нет `.mc`, updater или workflow в tracked tree; generic API docs не измерение FR165 | Реальные transfer/geometry/digest/parse/persist/reboot/fault/RAM/storage measurements, tasks2.2/4.4/4.5 |
| AOD и физическая эргономика |84 browser states относятся к active макету | Литые пиксели, burn-in, аппаратная читаемость, sleep/disabled gesture и батарея на FR165, task5.5 |
| Глобальное наполнение |839-record source audit сохранён; пять рисунков — частичный pack | Official supplement closure, все требуемые artwork/marks/sites/maps и dated denominators, task4.3 |
| Локализация |36 draft locales, не native support | Реальные glyph/font/RTL/translation/fit checks; manifest/listing только qualified subset, task5.4 |
| Совместимость и бюджет |8KiB feed,1MiB artifact,64KiB ledger и90-day support — проектные числа | Измерить при полном global content и retention; конфликт не закрывать уменьшением охвата, tasks3.5/4.4/7.2 |
| Публикация | Нет native pilot, live publisher или Garmin disposition | Provider→Pages→phone→FR165, first/second validation/assets, PRG, approved Store install/settings/update, tasks6.1/7.1–7.3 |

Полнота требований к миру не равна полноте наполнения. Generic fallback — runtime
безопасность, не выполненная приёмка known-model artwork. URL Pages остаётся
примером до фактического enable/deploy/readback. MIT не выдаёт прав на SDK, чужие
логотипы/изображения или данные провайдера; их terms/notices проверяются отдельно.
Официальный SpaceFox бесплатен, MIT-права на коммерческие fork не урезаются.

## Проверка и границы результата

Структурная проверка, source bindings и retained checks фиксируются в [checks.json](checks.json).
Старые global/efficient-storage structural receipts относятся к прежним версиям
спеки и не переписываются; новые structural receipts заменяют только эту границу.
839-record archive, browser owners, tools и native-отсутствие проверяются отдельно.
Зелёные browser cases сохраняются без повторного запуска: документы не изменяют
их semantic inputs. Никакие compile/device/API/Store passes не выдумываются.

Первая попытка batch patch не нашла строку tasks.md, потому что предложение было
перенесено на две строки; diff подтвердил отсутствие частичного применения.
Другая patch-попытка содержала лишний отсутствующий design anchor. Обе исправлены
узкими точными изменениями, без rerun поведения или изменений frozen UI.
Путь apply_patch не используется как свидетельство продукта. Summary-парсер
retained query ожидал list вместо dict и упал; сам query успешно завершился.
Исправлен только парсер сохранённого результата:6passed, без повторного query
или rerun поведения.

Следующий native entry — resolve2.3, real verification ownership2.1 и FR165
qualification2.2. Спека пригодна как актуальный план, но готовность изделия,
допуск к использованию и публичный Store-релиз **не подтверждены**.
