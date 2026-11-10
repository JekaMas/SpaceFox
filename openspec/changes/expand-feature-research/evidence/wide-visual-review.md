# Wide metadata / five-route image-only review

## Scope and verdict

Inspected all ten actual JPG screenshots in `evidence/wide-images/` using `view_image`, `detail=original`: `scene0..4-group1/2.jpg`. Only those images were read. Source, metrics, JSON, author ratings, and other reviews were not consulted. No product files were edited.

**The five-route set is visually BLOCKED by D's missing visible marker in scenes0–3.** Those scenes have available coordinates and explicitly require a visible marker. D shows geography, but I cannot find a visible marker in any of them. A/B/C/E have visible markers. This is a role-completeness failure, independent of whether text sizing is acceptable.

The wide company stress does not reveal an obvious text-clipping or overlap blocker in the displayed samples. That positive observation does not cancel the missing marker.

## Visible marker evidence

| Proposal | Scene0 short RU | Scene1 wide-letter stress | Scene2 natural RU | Scene3 EN | Scene4 unknown time |
|---|---|---|---|---|---|
| **A** | Visible in globe | Visible in globe | Visible in globe | Visible in globe | Visible in globe |
| **B** | Visible in globe | Visible in globe | Visible in globe | Visible in globe | Visible in globe |
| **C** | Visible in right map | Visible in right map | Visible in right map | Visible in right map | Visible in right map |
| **D** | **Not visible** | **Not visible** | **Not visible** | **Not visible** | Not visible |
| **E** | Visible above/right of mission panel | Visible above/right of mission panel | Visible above/right of mission panel | Visible above/right of mission panel | Visible above/right of mission panel |

D's geographic image is readily visible to the right and below the panels, so this is not merely an absence of the entire geographic object. What is missing from the image is an identifiable point/ring marking the site. I cannot determine whether it was omitted, obscured, placed outside the visible area, or rendered in some other way. No implementation explanation is inferred.

The permission for scene4 to omit geography/marker when coordinates are absent does not apply to scenes0–3. D's scene4 alone would not establish a blocker under that exception; the four required-coordinate scenes do.

## Text, gaps, and circle edges

### Scene1: wide-letter legal stress

The company described by the task as 32 wide letters is visibly arranged in two lines in A–E. Neither line visibly runs through the circular edge, over another text role, or under a neighboring block. The title `Falcon 9 Block 5`, purpose `Исследование дальнего космоса`, four values, location `Казахстан · Тест Полёт`, and long countdown are visible in all five.

Repeated identical wide glyphs make an exact character-count audit from the image less reliable than checking against an independently supplied string. I confirm the observed two-line layout and lack of visible clipping; I do not certify an exact count or source-string equality from this screenshot alone.

In B/C the two company lines use much of the upper region but remain inside the arc and separate from the purpose. In A the company occupies two rows within the left mission block. In D the wider passport panel contains both lines and the purpose, although its geographic marker is not visible. In E the full-width central mission panel preserves the two rows and a separate purpose line.

### Natural RU, EN, and unknown time

Scene0 preserves the short rocket/company/purpose, four fields, location, clock, and countdown. Scene2 preserves `Парус Light 2`, `Лаборатория небесной механики`, `Калибровка звёздных датчиков`, and `Индонезия · Тест Парус`; the natural company and purpose are each visible as complete shown phrases.

Scene3 preserves `Cedar Mk II`, `Distant Orbit Research Centre`, `Auroral spectrum survey`, `Norway · Test Cedar`, and the EN countdown. The relatively wide numeric values remain separate. No clock digit is visibly cut.

Scene4 preserves `Вектор 27 Heavy`, `Орбитальные системы Меридиан`, `Проверка межспутниковой связи`, `Турция · Тест Лира`, and `Время уточняется`. The explicit unknown-time phrase remains visible and does not masquerade as a numeric countdown.

No text visibly passes outside the circle in these samples. A/D's left mission text and E's broad central panel approach their available horizontal regions more than in a sparse short-data layout, but the shown beginnings and endings remain visible. The purpose, values, location, and time remain separate. This is an observation about the submitted phrases, not a guarantee for arbitrary strings or the full source contents.

## Hierarchy and distinct utility

The five structures remain meaningfully different:

- **A:** time with a separate globe, then values and a left mission passport; calm and conventional.
- **B:** mission and purpose first, then values and large lower time between rocket and globe; strong launch-following route.
- **C:** mission identity above a colored central clock and right map, purpose below it, then values/location; expressive central-time route.
- **D:** top time, two-column values, left mission passport, rocket right, and a large geographic backdrop; instrument-panel route. Its geographic utility is incomplete while the site marker is not visible.
- **E:** full Earth as the scene, then distinct time/mission/value/location panels; strongest global space atmosphere, with more background detail and panel edges.

These are not merely palette substitutions. The wider metadata has not erased their structural differences. A/B remain visually calmer; C is more clock-dominant; D/E accept more geographic texture and panels. That is an editorial description, not evidence of measured reading speed or preference.

## Required next action and limits

**Repair D so that an identifiable marker is actually visible in scenes0–3, then inspect the changed D images before claiming a complete five-route visual freeze.** The marker must remain separate from mission, numeric, location, and countdown panels. Source coordinates or a technical claim that a marker exists are not substitutes for its visibility in the image.

There is no image-based reason here to require additional cosmetic repairs to A/B/C/E. Their visible text and marker observations should retain their present proof boundary; unrelated changes do not automatically invalidate them.

This review does not establish geographic accuracy, physical Garmin readability, exact source-string equality, all input lengths/languages, all configurations or statuses, child/adult preference, speed/error rates, AOD quality, animation, performance, battery, or technical implementation acceptance. The small dark AOD previews are insufficient for AOD approval.

**Final bounded result:** text-width/circle inspection shows no obvious blocker in the five samples per route; actual visible-marker inspection fails D in all four mandatory-coordinate scenes. The current five-route set therefore does not pass complete visual role acceptance.
