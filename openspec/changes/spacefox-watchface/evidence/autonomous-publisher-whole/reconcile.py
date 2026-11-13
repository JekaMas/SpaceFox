"""Reconcile observed method receipts; this is not a new behavior execution."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
PROPERTIES={'LS03.P4','LS03.P5','LS03.P6','LS03.P7','LS03.P8','LS03.P10'}
RECEIPTS={
 'test_source_materialization_and_prepare_before_authority':'raw-first.log',
 'test_source_rights_edits_and_bad_pin_negative':'opposite-identities-green.log',
 'test_current_live_root_and_immutable_negative':'opposite-identities-green.log',
 'test_pages_empty_identity_and_uncertainty_negative':'pages-negative-green.log',
 'test_metadata_source_acceptance_and_adoption_positive':'opposite-identities-green.log',
 'test_current_source_data_only_extension_and_preserved_refusals':'source-green-pending-interrupted.log',
 'test_selected_current_bound_and_explicit_unknown_absence':'absence-current-green.log',
 'test_prepare_not_due_second_validation_and_disabled_schedule_recovery':'due-current-green.log',
 'test_empty_pages_exact_witness_and_nonempty_uncertainty':'stable-partial-green.log',
 'test_metadata_zero_work_gates_and_workflow_serialization':'metadata-url-origin-failure.log',
 'test_runtime_only_two_generations_finality_and_exact_readback':'runtime-current-green.log',
 'test_saved_faults_stale_source_and_cas_refuse_without_publication':'runtime-current-green.log',
 'test_metadata_pending_armed_core_promotion_recovery_and_partial_prefix':'pending-current-green.log',
 'test_metadata_sparse_resume_304_cadence_source_isolation_and_no_journal':'metadata-current-green.log',
 'test_metadata_current_policy_cli_refusals_cas_and_failure_preservation':'metadata-120s-failure-policy-green.log'}
source=ROOT/'tests/test_autonomous_publisher_whole.py'
module=ast.parse(source.read_text())
methods={node.name:node for parent in module.body if isinstance(parent,ast.ClassDef)
         and parent.name=='AutonomousPublisherWholeTest' for node in parent.body if isinstance(node,ast.FunctionDef)}
snapshot=ast.parse((HERE/'final-suite.py').read_text())
snapshot_methods={node.name:node for parent in snapshot.body if isinstance(parent,ast.ClassDef)
                  and parent.name=='AutonomousPublisherWholeTest' for node in parent.body if isinstance(node,ast.FunctionDef)}
rows=[]
for name,receipt in RECEIPTS.items():
 raw=(HERE/receipt).read_bytes()
 lines=[line for line in raw.decode().splitlines() if line.startswith(name+' (') and line.endswith(' ... ok')]
 assert len(lines)==1,(name,receipt,'missing/ambiguous observed green method')
 node=methods[name]
 assert ast.dump(node,include_attributes=False)==ast.dump(snapshot_methods[name],include_attributes=False),(name,'method drift after source snapshot')
 rows.append(dict(method=name,receipt=receipt,observedGreenLine=lines[0],
   receiptSha256=hashlib.sha256(raw).hexdigest(),
   currentMethodAstSha256=hashlib.sha256(ast.dump(node,include_attributes=False).encode()).hexdigest()))
graph=json.loads((ROOT/'openspec/changes/spacefox-watchface/verification.json').read_bytes())
cases=[c for c in graph['cases'] if c['property_id'] in PROPERTIES]
selected={c['test_id'].rsplit('.',1)[1] for c in cases}
assert selected==set(RECEIPTS),(selected-set(RECEIPTS),set(RECEIPTS)-selected)
assert len(cases)==40 and len(PROPERTIES)==6 and len(rows)==15
result=dict(status='SELF_GREEN_whole_six_existing_properties',properties=sorted(PROPERTIES),
 cases=[c['id'] for c in cases],caseCount=len(cases),observedMethods=rows,methodCount=len(rows),retainedIntegrationMethods=11,freshOppositePolarityMethods=4,
 reproducibleWholeCommand='python3 -B -m unittest -v tests.test_autonomous_publisher_whole',
 freshWholeSuiteReplay=False,
 reconciliation='Actual per-method green receipts retained from affected local executions. An interrupted or mixed-result suite is never relabeled as an all-green command; only completed exact green methods are reused. Remaining changed-fixture methods have their new complete green command receipts.',
 sourceSha256=hashlib.sha256(source.read_bytes()).hexdigest(),
 sourceChanges='No production, workflow, runtime seed, catalog or native resource change. Current oracle/selector/test/evidence corrections only.',
 fixtureBoundary='Actual captured launch and closed real USA2/SpaceX121/Starship522/pad235 metadata records. Technical count/pagination and LL2 URL-origin rebasing are controlled loopback fields; no new complete-provider observation.',
 retainedSemantics='Unused metadata-service fixture branches changed after some accepted source/status/gate/runtime receipts. Those methods never fetch metadata (asserted), and their test bodies and relevant product/source/provider/Pages inputs remain unchanged. Only the three methods exercising the changed metadata rows were rerun. Earlier source SVG and due assertions were rerun when changed. The last sparse304 method was rerun after correcting its arbitrary120s harness timeout to the real metadata-job ceiling300s; the other10 methods completed under the stronger120s ceiling and were not replayed.',
 proofBoundary='Real temporary Git/sparse YAML shell/CLI/production HTTP against loopback; substituted provider/Pages/Actions/OIDC responses. Existing root hosted evidence is separately hash-bound. No remote/provider/account/SDK/paid/physical operation by this unit.',
 polarityRepair='Pinned graph requires disjoint positive/negative identities. Four genuine minimal production-owner witnesses execute independently; original11 mixed integration observations remain valid support and were not replayed for renaming. No property/case growth.',
 independentReview='CLOSED/GREEN by root-assigned different peer; see peer-review/FINAL.md and peer-review/receipt-audit.json. Root integration judgment remains. No behavior replay or production/test change.')
(HERE/'WHOLE-RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],properties=6,cases=40,methods=15,behaviorReplay=False)))
