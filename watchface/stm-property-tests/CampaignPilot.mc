import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
// Harness monotonic time measures test execution only; every business clock,
// storage, timer and service in the tested owners is independently faked.
(:typecheck(false)) function campaignBatch(owner, seed, count){
 if(owner==0){return runGeneratedDisplayOwners(seed,count);}
 if(owner==1){return runGeneratedRequestOwners(seed,count);}
 if(owner==2){return runGeneratedSceneOwners(seed,count);}
 if(owner==3){return runGeneratedStorageOwners(seed,count);}
 if(owner==4){return runGeneratedTemporalService(seed,count);}
 if(owner==5){return runGeneratedCacheMapOwners(seed,count);}
 if(owner==6){return runGeneratedViewLifecycle(seed,count);}
 if(owner==7){return runGeneratedForegroundDelivery(seed,count);}
 if(owner==8){return runGeneratedSelectedFields(seed,count);}
 if(owner==9){return runGeneratedFitnessOwners(seed,count);}
 if(owner==10){return runGeneratedReminderOwners(seed,count);}
 if(owner==11){return runGeneratedSourceSwitch(seed,count);}
 if(owner==12){return runGeneratedArtLease(seed,count);}
 if(owner==13){return runGeneratedWakeOwner(seed,count);}
 if(owner==14){return runGeneratedServiceFailure(seed,count);}
 Test.assertMessage(false,"unknown campaign owner");return 0;
}
(:test,:typecheck(false)) function campaignPilot(logger){
 PbtMetrics.assertions=0;PbtMetrics.skipped=0;PbtMetrics.coverage={};var first=PbtConfig.FIRST_SEED;var seed=first;var events=0;var batches=0;
 logger.debug("PBT_CAMPAIGN_BEGIN worker="+PbtConfig.WORKER+" owner="+PbtConfig.OWNER+" first="+first);
 var start=System.getTimer();var elapsed=0;var nextReport=60000;
 while(elapsed<PbtConfig.DURATION_MS){events+=campaignBatch(PbtConfig.OWNER,seed,8);seed+=8;batches+=1;elapsed=System.getTimer()-start;
  if(elapsed>=nextReport){logger.debug("PBT_CAMPAIGN_PROGRESS owner="+PbtConfig.OWNER+" next="+seed+" events="+events+" productive_ms="+elapsed);nextReport+=60000;}}
 Test.assert(events>0&&seed>first&&elapsed>=PbtConfig.DURATION_MS);
 logger.debug("PBT_CAMPAIGN_COVERAGE "+PbtMetrics.coverage+" assertions="+PbtMetrics.assertions+" skipped="+PbtMetrics.skipped);
 logger.debug("PBT_CAMPAIGN_END worker="+PbtConfig.WORKER+" owner="+PbtConfig.OWNER+" first="+first+" next="+seed+" batches="+batches+" events="+events+" productive_ms="+elapsed);return true;
}
(:test,:typecheck(false)) function campaignParameterSmoke(logger){
 for(var owner=0;owner<15;owner+=1){var n=campaignBatch(owner,1001+owner*100,8);Test.assertMessage(n>0,"campaign owner had no events");}
 logger.debug("PBT_CAMPAIGN_SMOKE owners=15 seeds_per_owner=8 fresh_seed_per_owner=true after_each=true");return true;
}

// Exact seed reproduction runs the same production seam and independent model.
(:test,:typecheck(false)) function campaignReplay(logger){
 var n=campaignBatch(PbtConfig.OWNER,PbtConfig.FIRST_SEED,1);Test.assert(n>0);
 logger.debug("PBT_REPLAY owner="+PbtConfig.OWNER+" seed="+PbtConfig.FIRST_SEED+" events="+n);return true;
}
