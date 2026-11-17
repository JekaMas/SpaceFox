import Toybox.Test;

// Reuse the two existing production-bound sequence generators at their short
// selected scope after the wake and metric-source contracts changed.
(:test,:typecheck(false)) function physicalAffectedStateSequences(logger){
 Test.assert(generatedViewLifecycle(logger));
 Test.assert(generatedFitnessOwners(logger));
 Test.assert(coldLowAcquiresOneFieldSnapshot(logger));
 logger.debug("PHYSICAL_AFFECTED view_and_fitness_generators plus cold_low=true");return true;
}
