# Resources, supporting files and engineering costs

Every base-tree file has a row in FILE-INVENTORY.csv, with its Git blob, source byte size, package, review method and disposition. This is explicit about scope: full native reads/resource-path publisher review, static per-function supporting-tool indexes, resource metadata, and unexecuted historical evidence are different evidence levels. Nothing is labeled manually reviewed solely because it was inventoried.

## Data and compiled resources

- 275native resource files /3,351,100sourcebytes:173PNG,6FNT,53JSON,43XML. RESOURCE-INVENTORY.csv gives every file a SHA/type/dimensions/metadata row.72bundled active maps195x195 and72LOW outlines390x390 are alternatives; only matching map(s) are referenced by current renderer.391x391restmask is deliberate shifted/pixel-rest coverage, not an accidental extra fullscene.
- GeneratedNativeAssets retains6NativeModel wrappers,54NativeMap objects,18extra centerpairs packed144B and6iconresourceIDs. Resource IDs do not imply that every bitmap is loaded. **MEM-04 / moderate optimization / STATIC:** extending the packed-coordinate approach to the54map wrappers can reduce resident object metadata without changing map pixels; quantify release heap before/after and retain exactpointidentity/lookup behavior.
- Only fiveLocale dictionaries are selectable/qualified in production;36locale resources remain intentional historical/future assets per userdirection. LocalePresentation loadsonecurrentdictionary. FieldText cachesnone, GraphemeProperties decodes1829bytes once. FullUAXpropertytable isn't a new displaystress campaign; it is an existing dependency. Non-ASCII range lookup linearcost only arises at fitted cluster boundaries.
- Count31,Label17,Label21FNTdefinitions exist but current renderer uses vectors for those roles. **ASSET-01 / low / STATIC:** no current product Rez.Fonts call to these3IDs found; compiler pruning/package-byte impact not measured. Check exact packaged resource table before removal; do not claim3fontimages are resident merely from XML.
- 961catalog/artwork/corpus/locale inputs /18,799,521sourcebytes. Publisher fullcatalog/region inputs stay offwatch; watches receive selected text + bounded immutable closure. Historical identities/provenance in source are not native runtimelegacy compatibility.

## Browser research

127files /2,432,570bytes, never part of nativeSourcePath.94JS/HTML/shell/Java supporting files were resource-site indexed (including vendored files, whose internals were not re-reviewed). Research galleries can retain campaigntrials, manySVG/DOMfaces and decompressedcampaignJSON; cost is intentional desktopexperiment lifetime, not watchheap. Rocket-models preview loadsallSVG viaPromise.all and retainsDOMtemplates; selectednativeproducerdoesnotdothis.

**WEB-01 / low historical embed / STATIC:** prototype/mission.js globalopenai:set_globals listener closesoverroot/state and is neverremoved. Its1sinterval checks disconnectedroot and clearsitself,timer,RAF,ResizeObserver, butnotthiswindowlistener. In repeatedmountswithinonesamewindow thelistenercanretainoldpreviewclosure. Wholewindowunloadreleasesit; currentnativepreviewisstatic and doesnotruntheoldmissionwidget. Fixonlyifthisembedreturns, not as a watchoptimization.

## Host engineering and tests

- 163 tools have individual entries in TOOLS.md/TOOL-INVENTORY.json;150 are Python, 12 JavaScript and one Java adapter (including vendoredD3/TopoJSON). External-capable sideeffects are explicit in functionindexes; no arbitrary recipe was executed.
- 431nonhistoricalPython files parsed successfully withast withoutimport/execution:19publisher,150tools,261test/fixturehelpers,1catalogdatahelper. There are1112test_*functiondefinitions in hosttest/fixturepaths; this is NOT1112newtestexecutions or coverageproof.
- Base contains15,636historicalevidencefiles /1,270,565,240bytes,96.43%ofsourceblobbytes. These are retained originalpositive/negative receipts. A full materializedcheckout is expensive; useexisting sparseproductionclosure. qualify-current-motion workflow currentlyspecifiesfullcheckout. CompressedGittransferbytes/inodeI/O/clonewalltimearenotmeasured. Do not deletefailures/provenance to manufacture smaller tests.
- **ENG-01 / low / STATIC:** release.py snapshots/hashescompilerinputs beforeandaftereachof10PRG+IQinvocations,thenfinalverification; this is deliberate mutationdefense, not automatically redundant. Candidate/official modes alwaysrecompile. Optimizing promotion requiresexactidentity/source/flags/signature equivalence; don't blindly removehashguards.
- **ENG-02 / moderate operator-only / STATIC:** display_corpus.http_get and verify_native_text_http use sockettimeouts, not killabletotaloperationdeadlines. A slowbody can exceedthe nominal60s/15s whilemakingprogress. They are notscheduledproviderowners. ProductionHTTPuses killable20sworker instead.
- **CLEAN-02 / low / STATIC:** build_private_beta.py is pinnedto0.1.4andnineprofiles and cannotbuildcurrent0.1.18ten-profilebaseline. It is an obsoleteoperatorentrypoint, notusedbycurrentrelease. Keepunderlegacycleanup findings; noexecutionattempt orcurrentreleasefailureclaimed.
- Oldnativeprobe/toolsare notcompiledintoproduction,butmanyarecurrentproofinputs importedbyreceiptreaders. They cannot safely be deleted merely from old names; dependencyclosure must be assessed before retiring them. Currentaudit never reran them.

## Measurement gaps

No newSDKlane,physicalwatch,phone,CDN/providerrefresh orCIexecutionwasused. Applicationheapretainedmeasurements are exactreleaseidentity finitecases. GraphicsPoolpeak,pertransitionreclaimednativebytes,longrunrefcounts,actualbatteryenergy,watchwalltime/framep95,pairinglatency and UbuntuCIpeakRSSremainOPEN. A source bound or offlinehostsamplecannotclose thosephysicalmetrics.
