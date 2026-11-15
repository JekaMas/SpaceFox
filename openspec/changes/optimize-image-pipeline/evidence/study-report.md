# Image representation study

140 retained assets; training 17, held out 123 (including all additional inventory). Configurations: {'generation-1': 16, 'generation-2': 8, 'generation-3-finalists': 4}; filtered asset/config pairs: 313. Exact decode succeeded for each unfiltered pair.

Training ranking, generation 1: 2/2, 3/2, 4/2, 5/2, 6/2, 8/2, 10/2, 12/2, 16/2, 20/2, 24/2, 32/2, 40/2, 48/2, 64/2, 1/2

Training ranking, generation 2: 9/8, 11/8, 13/8, 15/8, 17/8, 19/8, 21/8, 7/8

QOI is a tested pixel-stream implementation with an independently decoded stream; the reported file size adds 22 standard header/end bytes as an estimate, without emitting a full conforming file. Source PNG size is a separate file measurement, not a watch allocation or transfer cost. Host timings and alternative codecs are not watch performance or supported native formats. CSV records each measured asset/configuration.
