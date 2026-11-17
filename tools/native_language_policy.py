"""Source-bound finite software admission, separate from human/device review."""
import hashlib,json,re,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
OWNERS=('tools/native_language_policy.py','tools/build_native_localization.py','tools/build_watchface.py',
        'tools/display_corpus.py','tools/current_language_probe.py','tools/spacefox/provider.py','tools/spacefox/catalog.py',
        'watchface/source/LocalePresentation.mc','watchface/source/SceneRenderer.mc',
        'watchface/source/SceneSettings.mc','watchface/source/SpaceFoxView.mc',
        'watchface/source/WatchClock.mc','watchface/source/Fitness.mc',
        'watchface/source/ScheduleState.mc','watchface/source/SceneContext.mc',
        'watchface/source/FeedScene.mc','watchface/source/generated/LocaleGraphemes.mc')

def input_paths(catalog,root=ROOT):
 """Exact common typography and primary text closure, including resource bindings.

 SceneStrings/manifest availability is generated from admission itself and is
 excluded to avoid a hash cycle. Their generator, locale JSON bindings, settings,
 text owners and independent jungle/toolchain inputs remain bound.
 """
 root=Path(root).resolve()
 rows=catalog['locales'];primary=set(catalog['supportPolicy']['primaryLocales']);paths=list(OWNERS)
 paths.extend(('watchface/monkey.jungle','watchface/toolchain-lock.json',
               'watchface/resources/settings/settings.xml','watchface/resources/settings/properties.xml'))
 def dependency(binding,filename):
  if not isinstance(filename,str) or not filename or Path(filename).is_absolute():raise ValueError('invalid software resource dependency')
  path=(root/Path(binding).parent/filename).resolve()
  if not path.is_relative_to(root) or not path.is_file():raise ValueError('software resource dependency unavailable: '+filename)
  return path.relative_to(root).as_posix()
 def bindings(name,tag):
  paths.append(name)
  try:items=list(ET.parse(root/name).getroot().iter(tag))
  except (OSError,ET.ParseError) as error:raise ValueError('invalid software resource binding: '+name) from error
  result={}
  for item in items:
   identity=item.get('id')
   if not identity or identity in result:raise ValueError('duplicate/missing software resource ID: '+name)
   result[identity]=item.get('filename')
  return result
 locale_binding='watchface/resources/json/locales.xml';locale_files=bindings(locale_binding,'jsonData')
 for index,row in enumerate(rows):
  if row['id'] not in primary:continue
  code={'chs':'zhs','cht':'zht'}.get(row['garmin'],row['garmin']);folder='resources' if row['id']=='en' else 'resources-'+code
  paths.extend(('locales/'+row['id']+'.json',dependency(locale_binding,locale_files.get('Locale'+str(index))),'watchface/'+folder+'/strings/strings.xml'))
 grapheme_binding='watchface/resources/json/graphemes.xml';grapheme_files=bindings(grapheme_binding,'jsonData')
 paths.append(dependency(grapheme_binding,grapheme_files.get('GraphemeProperties')))
 font_binding='watchface/resources/fonts/fonts.xml';font_files=bindings(font_binding,'font')
 # Follow actual Rez.Fonts references, then BMFont page references. Unused
 # legacy font atlases and best-effort translations do not enter this closure.
 font_ids=set()
 for name in OWNERS:
  if name.endswith('.mc'):font_ids.update(re.findall(r'\bRez\.Fonts\.([A-Za-z0-9_]+)',(root/name).read_text()))
 for identity in sorted(font_ids):
  font=dependency(font_binding,font_files.get(identity));paths.append(font)
  pages=re.findall(r'^page\s+[^\n]*\bfile="([^"]+)"',(root/font).read_text(),re.MULTILINE)
  if not pages:raise ValueError('software font has no bitmap pages: '+font)
  paths.extend(dependency(font,page) for page in pages)
 return tuple(dict.fromkeys(paths))

def validate_generated_locale_source(root,catalog,qualified,*,include_availability=True):
 """Verify generated mappings without a proof→availability→proof hash cycle."""
 try:
  from tools.build_native_localization import scene_strings
 except ModuleNotFoundError:
  from build_native_localization import scene_strings
 path=Path(root)/'watchface/source/generated/SceneStrings.mc'
 try:actual=path.read_text()
 except OSError as error:raise ValueError('generated locale source unavailable') from error
 expected=scene_strings(catalog['locales'],qualified)
 if not include_availability:
  def static(source):
   # Exclude only the return expression of the one generated availability
   # function. All ID/code/resource mappings and every other byte stay checked.
   result,count=re.subn(r'(?m)^( function available\(index as Number\) as Boolean \{return )[^{}\n]*(;\})$',r'\1<admission>\2',source)
   if count!=1:raise ValueError('generated locale availability function differs')
   return result
  actual=static(actual);expected=static(expected)
 if actual!=expected:raise ValueError('generated locale source differs from source-bound admission')

def software_locales(root,catalog=None):
 """Admit only the one current five-primary proof, without historical dispatch."""
 root=Path(root).resolve();catalog=catalog or json.loads((root/'locales/catalog.json').read_text())
 from tools.current_language_admission import validate
 return validate(root,catalog)
