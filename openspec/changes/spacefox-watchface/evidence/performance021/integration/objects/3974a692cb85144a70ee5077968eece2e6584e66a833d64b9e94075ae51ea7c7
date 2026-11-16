// Current producer SFR1M root; test-only mutations do not alter source text.
(:test,:typecheck(false)) function currentIdentityPositive(log){
 var s=new RefreshFaultStore(null);unresolvedSeed(s);var p=new NativeBridgeFeed(unresolvedResource("real2"),1794551192l,s);
 var b=new NativeSfrBuild(s,"https://fixture.invalid/unresolved",p);
 Test.assert(b.result.selectionHash.equals("41abf304fe69c7ed2dd628e6946dbe48256e1919e375de41a0fdffa48cd4ff3f"));
 Test.assert(b.scene["launchId"].equals("ll2:launch:a6bc9339-1a98-4483-9cdd-738768401c2e"));
 Test.assert(b.scene["modelId"].equals("ll2:configuration:515")&&b.scene["siteId"].equals("ll2:site:233"));
 log.debug("current SFR1M producer root binds launch/model/site and expected selection digest");return true;
}
(:test,:typecheck(false)) function currentIdentityNegative(log){
 var s=new RefreshFaultStore(null);unresolvedSeed(s);
 for(var i=0;i<5;i+=1){var p=new NativeBridgeFeed(unresolvedResource("real2"),1794551192l,s);p.bridge["ids"][i]=i==4?"ll2:country:999999":null;
  var rejected=false;try{new NativeSfrBuild(s,"https://fixture.invalid/unresolved",p);}catch(e){rejected=true;}Test.assertMessage(rejected,"root identity mismatch "+i);}
 var p=new NativeBridgeFeed(unresolvedResource("real2"),1794551192l,s);var b=new NativeSfrBuild(s,"https://fixture.invalid/unresolved",p);
 b.scene["roles"]["rocket"]={"entityId"=>"ll2:configuration:999999","descriptor"=>["a",1]};var rejected=false;
 try{b.prepareRole("rocket");}catch(e){rejected=true;}Test.assert(rejected);
 log.debug("five typed root mismatches and wrong rocket role owner are rejected");return true;
}
