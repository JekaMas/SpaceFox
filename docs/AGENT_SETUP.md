# Свой SpaceFox: инструкция владельцу и агенту

Оригинальные инструкция и спека — [MIT](../LICENSE). Выбрана схема
**GitHub Actions → статический GitHub Pages feed → Garmin Connect → FR165**.
AWS, свой сервер, отдельный домен и регулярные LLM-вызовы не нужны.

**Состояние на 2026-11-11:** есть спека, браузерные макеты и частичные ассеты.
Нативного приложения, `tools/update_feed.py`, production catalog/exporter и
`.github/workflows/update-feed.yml` нет. Ниже план, не готовый установщик.
[Разработка/выпуск](RELEASE_AND_UPDATES.md), [единые задачи](../openspec/changes/spacefox-watchface/tasks.md).

## Перед настройкой

Проверить наличие реального native/updater/workflow. Недостающее реализуется в
отдельной разрешённой задаче, а инструменты не устанавливаются незаметно. Официальный
издатель — взрослый владелец со своим Garmin developer account; возрастное условие
аккаунта и целевого использования подтверждены владельцем для текущего экземпляра;
дополнительных возрастных уточнений не требуется. Точные возраста не сохраняются.
Для других экземпляров неизвестный возраст сам по себе не блокирует реализацию. Отдельное правило under13 касается аудитории/использования, включая
известное использование ребёнком общего приложения; проверить его при подготовке
выпуска, не считать взрослого издателя или личный PRG исключением. Частные возраста
не публиковать.
[Полный текст guidelines](https://developer.garmin.com/connect-iq/articles/app-review-guidelines/Overview.html).

После официального выпуска другой семье достаточно бесплатного Store-приложения
и своей копии **издателя**, без SDK и ключа автора. Пока Store-релиза нет, личный
пилот требует отдельной квалифицированной сборки/установки PRG. Native fork со
своими изменениями использует собственные UUID/key; чужая копия не обновляет
официальную Store-идентичность. Не принимать соглашения за владельца незаметно.

## Как будут приходить изменения

1. Cron может просыпаться раз в15минут, но LL2 опрашивается только по сроку:
   обычно раз вчас, сT−2ч до неподтверждённогоT+30мин — раз в15минут; неизвестное
   время — раз вчас. Затем часовой режим. Не-due wakeup не делает запрос,
   commit или deployment. Fast5мин — отдельная настройка с подходящим cron.
2. Сохраняется проверенный компактный snapshot, затем полный статический deploy:
   `data/v1/schedule.json`, ограниченный slice manifest и неизменяемые файлы по
   digest. Schedule≤8192UTF-8байта; реальные RAM/parser/storage могут потребовать
   меньшего предела. Полный мировой manifest часы не загружают.
3. Фоновый сервис часов получает данные через телефон по60/15-минутной политике.
   `UTC старта − текущий UTC часов` считается локально на redraw/wake; сетевых
   запросов/записей в хранилище на каждом тике нет. Сон не накапливает ошибку таймера.
4. Перенос того же запуска делает отсчёт янтарным; старение добавляет пунктир
   под ним. Эти признаки независимы. Нет `!`, перечёркнутой тучки или постоянной
   строки обновления. Неизвестное время даёт неопределённость, ноль — ожидание
   подтверждения. Анимация не свидетельствует о настоящем взлёте.

Два часовых опроса могут добавить почти2часа обнаружения изменения, два
15-минутных — почти30минут, плюс GitHub/CDN/связь. Сам локальный отсчёт идёт по
сохранённому времени. Порог старения —3часа обычно и45минут в ближнем окне,
по умолчанию3цикла издателя. Возраст относится к **проверке источника по записи**;
старыйHTTP200/304, сборка графики или проверка других записей его не обновляет.
Уже stale-запись не становится свежей от выхода из ближнего окна.

## Настройка экземпляра агентом

1. **Проверить владельца и код.** Для текущей семьи — `JekaMas/SpaceFox`; для
   другой — её fork/копия. Проверить default branch, ожидаемую ревизию, реальный
   updater и schemas; обновления upstream сначала просматривать/проверять.
   Source commit не означает обновление установленного приложения.
2. **Подготовить durable feed-state.** Отдельная ветка содержит active/pending,
   возраст/переносы, source/catalog/tool revisions, generation, due и бюджет.
   Первичный bootstrap явный; текущий ledger≤64КиБ, история Git контролируется
   отдельно. После bootstrap потеря state останавливает публикацию. CDN/cache/
   expiring artifact не единственные копии. Автоматический force-prune запрещён.
3. **Настроить Actions/Pages.** Workflow в default branch, cron со смещением от
   начала часа и manual dispatch; у fork проверить включение Actions. Только
   standard public runner. Source/PR checks contents:read; writer feed-state —
   contents:write; deploy — pages:write/id-token:write, environment github-pages.
   Проверить branch/environment rules; ключ Garmin data workflow не нужен.
4. **Настроить общий бюджет и порядок.** Один concurrency group для schedule,
   catalog и manual deploy с cancel-in-progress:false, плюс expected-base/CAS и
   монотонные поколения. Резервировать quota в Git **до** запроса. Основные poll
   дают1или4запроса/час; optionalfast≤12steady/час. Detail/pagination/retry/manual
   делят тот же документированный анонимный бюджет15/час и backoff. Потерянная
   reservation остаётся израсходованной; смена runner/IP не обходит лимит.
5. **Проверить и опубликовать целый candidate.** Durable pending — до deploy;
   полный Pages artifact содержит schedule и все current/retained совместимые
   assets, без raw dumps/SDK/макетов. Начальный budget≤1МиБ, artifact retention1день;
   конфликты с global coverage/90-дневной совместимостью решать явно, не урезая
   охват незаметно. Custom upload/deploy, exactHTTPS readback, затем CAS promotion.
   Сбой сначала reconciles Git active/pending/live; старый run не перезаписывает новый.
6. **Получить две настоящие проверки.** Вручную проверить JSON, digests и ссылки,
   затем следующий due poll. Unchanged content всё равно получает новую реальную
   source validation. Провайдерская ошибка её не меняет. Один зелёный workflow
   не доказывает живой HTTPS, а один CDN readback не доказывает все edge-кеши.
7. **Настроить часы.** `FeedBaseUrl` из Pages именно этого репозитория. Пример
   будущего адреса: `https://jekamas.github.io/SpaceFox/`, schedule —
   `data/v1/schedule.json`. До включения это пример, не подтверждённый endpoint.
   Исходный URL пустой: время/поля и bundled fallback работают до setup/синхронизации.
   При смене URL launch state изолируется; verified content может переиспользоваться.
8. **Проверить действительный FR165.** Телефонная доставка, reboot/offline, old200/
   304, перенос/unknown, два asset revisions и исправленная точка, malformed/
   interrupted/unsupported update, storage-full, AOD и settings migration. Сохранить
   firmware/source/schema, реальные наблюдения и точные оставшиеся ограничения.

В анонимном LL2-режиме ключ не нужен. Если владелец позднее выберет ключ,
отдельно квалифицировать квоты и хранить его только в GitHub Secrets; не в часах,
JSON, исходниках/артефактах. Health, user GPS и личность семьи не отправляются.
Статические файлы публичны; обычные запросы видит выбранный хост, поэтому privacy
notice не обещает отсутствие у хоста технических access logs.

## Обновления кода и ассетов

Новые поддерживаемые rocket/site/mark/map данные добавляются через один catalog
workflow без layout switch и второго списка моделей. Сначала validate/rights,
потом build/digest/slice/deploy. Базовая native проба — ограниченные JSON-примитивы
и трансформации, не исполнение SVG/MonkeyC. Bitmap path и общий codec выбираются
после FR165-измерений. Active/staging/recovery bytes ограничены, activation целиком;
сбой оставляет прежнюю версию. Generic fallback не закрывает global artwork gaps.

Новая логика, permissions, fonts или неизвестные renderer operations требуют новой
подписанной native версии. Издатель сохраняет current+previous wire majors и
совместимые assets минимум90дней после объявления перехода. App settings сохраняются
версионируемой миграцией; несовместимость объясняется в настройках без новых badges.
Код исправляют более высокой signed версией; asset rollback — новым поколением
со старым проверенным набором. Source freshness при этом не обновляется.

## Если обновления остановились

- Часы продолжают локальный отсчёт по кешу, показывают старение пунктиром; перенос
  сохраняется. Ноль без подтверждения не означает взлёт.
- Проверить телефон, **source validation**, active/pending ветки feed-state и
  Actions/deployment; старый публичный JSON может возвращатьHTTP200.
- GitHub cron может задержаться/пропасть, а после60дней неактивности отключиться.
  Не обещать, что feed-state commits гарантированно отменят это правило.
  Проверить/включить workflow, запустить вручную и подтвердить новый source age
  черезHTTPS и на часах. Fork может изначально требовать включения расписания.
- Не сбрасывать ledger/квоту/переносы и не подделывать timestamp для «починки».
  Восстановить pinned candidate из Git/catalog, не полагаться на expired artifact.
  Не переключать часы на чужой feed автоматически и не увеличивать платные лимиты.

Локальный агент/планировщик возможен позднее с тем же deterministic updater,
но требует включённого компьютера и общей state/serialization/quota; это не default.

## Готовое поручение агенту

> Подготовь мой личный SpaceFox для FR165 по MIT-спеке и docs/AGENT_SETUP.md.
> Публикуем от моего взрослого developer account. Проверь текущие правила выпуска
> и наличие реализации; неизвестный возраст пользователя не блокирует разработку.
> Отсутствующее не выдавай
> за готовое. Для released official app настрой мой publisher fork, standard
> Actions, durable feed-state, custom Pages и FeedBaseUrl без ключа автора/SDK.
> Для ещё не выпущенного приложения отдельно квалифицируй native PRG, не обещая
> Store-доступности. Проверь quota/recovery/compatibility, две source validations
> и asset revisions, HTTPS и реальные часы. AWS и регулярные LLM не нужны.
> Не включай оплату, не публикуй private данные/ключи; сохрани evidence и ограничения.

Источники и дата сверки — в [реестре](../openspec/changes/spacefox-watchface/evidence/final-review/sources.md).
Среди них: [LL2 quota](https://github.com/TheSpaceDevs/Tutorials/blob/main/faqs/faq_TSD.md),
[Garmin background](https://developer.garmin.com/connect-iq/articles/core-topics/Backgrounding.html),
[GitHub schedule](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[custom Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).
