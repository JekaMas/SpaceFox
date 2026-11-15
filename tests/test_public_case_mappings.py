"""Public case-ID migrations with explicit canonical component assertions."""
import unittest

class PublicMappedCases(unittest.TestCase):
    def check(self, names):
        result = unittest.TestResult()
        unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(name) for name in names).run(result)
        self.assertEqual(result.skipped, [], 'mapped proof may not skip')
        self.assertTrue(result.wasSuccessful(), str(result.errors + result.failures))

    def test_vc02_p1_s01_positive_current(self):
        self.check(['tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_gravity_identity_uses_retained_source_and_review', 'tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_independent_lifecycle_batch_preserves_facts_and_art'])

    def test_vc02_p1_s02_positive_current(self):
        self.check(['tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_blk3_is_source_qualified_and_distinct_from_prior_sarge', 'tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_named_family_selection_preserves_unknown_variant'])

    def test_ls05_p4_s01_positive_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_durable_latches_and_publication_preserve_source_ages', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_null_zero_negative_and_future_selection_epochs', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_current_projection_deterministic', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_current_projection_preserves_timing_phase', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_missing_optional_context_current_artifact', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_real_utf8_launch_survives_current_projection'])

    def test_ls05_p4_s03_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_invalid_current_artifacts_keep_active_and_source', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_invalid_source_coordinate_preserves_accepted_artifact'])

    def test_vc05_p3_c10_negative_current(self):
        self.check(['tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_gate_rejects_caller_modified_registry', 'tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_gate_rejects_replaced_capture_even_if_inventory_matches', 'tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_known_art_gap_preserves_real_event_fallback_and_fails_gate', 'tests.test_current_catalog_art_closure.CurrentCatalogArtClosureTest.test_source_cohort_gate_refuses_missing_wrong_art_and_flags'])

    def test_vc20_p1_c02_negative_current(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p1_corrupt_scene_negative', 'tests.test_display03_receipt_binding.CurrentMapReceiptTest.test_current_map_negative', 'tests.test_sfr1m_offline_current.Sfr1mOfflineCurrent.test_corrupt_digest_rejected'])

    def test_vc20_p1_c03_positive_current(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p1_selected_scene_positive', 'tests.test_display03_receipt_binding.CurrentMapReceiptTest.test_current_map_positive', 'tests.test_public_proof_portability.PublicProofPortabilityTest.test_ordinary_full_scene_retained_source_binding', 'tests.test_sfr1m_offline_current.Sfr1mOfflineCurrent.test_current_raw_pixels_identity_age_and_bounds'])

    def test_vc20_p3_motionwhole_hostclosure_negative_current(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p3_refusal_negative', 'tests.test_durable_delivery_whole.DurableDeliveryWholeTest.test_missing_previous_catalog_cannot_promote_pending'])

    def test_vc20_p2_motionwhole_hostgeneration_positive_current(self):
        self.check(['tests.test_current_motion_publisher.CurrentMotionPublisherTest.test_actual_launch_whole_publication_and_refusal', 'tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p2_source_update_positive'])

    def test_vc20_p1_motionwhole_hostsparse_positive_current(self):
        self.check(['tests.test_current_global_context.CurrentGlobalContextTest.test_tracked_context_source_closure_positive_and_negative', 'tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p1_selected_scene_positive', 'tests.test_display03_receipt_binding.CurrentMapReceiptTest.test_current_map_positive', 'tests.test_public_proof_portability.PublicProofPortabilityTest.test_ordinary_full_scene_retained_source_binding', 'tests.test_sfr1m_offline_current.Sfr1mOfflineCurrent.test_current_raw_pixels_identity_age_and_bounds'])

    def test_ls05_p1_s01_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_invalid_current_artifacts_keep_active_and_source', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_invalid_source_coordinate_preserves_accepted_artifact', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_regressing_source_rejected_without_replacement'])

    def test_ls04_p2_s01_positive_current(self):
        self.check(['tests.test_current_motion_publisher.CurrentMotionPublisherTest.test_shared_rolling_hour_quota_survives_reopen', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_local_http_due_origin_304_and_429'])

    def test_ls04_p2_s01_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_throttled_backoff_blocks_manual_version_without_write', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_uncertain_reservation_survives_reopen_without_refund'])

    def test_ls04_p3_s04_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_duplicate_later_page_rejects_atomic_batch_negative', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_explicit_page_cap_reports_partial_positive'])

    def test_ls11_p3_s02_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_regressing_source_rejected_without_replacement', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_decoded_boundary_negative'])

    def test_ls11_p3_s10_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_optional_failures_preserve_primary_and_old_source', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_two_hour_429_backoff_survives_quota_window_rollover'])

    def test_ls11_p3_s26_negative_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_fixed_now_survives_delayed_response', 'tests.test_schedule_producer_whole.ScheduleProducerWholeTest.test_origin_age_and_future_rejection'])

    def test_ls11_p3_s32_positive_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_current_content_only_prepare_preserves_source_age_without_provider', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_unchanged_fresh_origin_renews_only_validation'])

    def test_ls11_p3_s33_positive_current(self):
        self.check(['tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_empty_cached_200_preserves_selection_epoch', 'tests.test_schedule_producer_transport.ScheduleProducerTransportTest.test_optional_429_preserves_primary_and_omitted_age'])

    def test_ls05_p8_s01_negative_current_proof_controls(self):
        self.check(['tests.test_current_format_acceptance.CurrentFormatAcceptanceTest.test_ls05_p8_s01_negative_current', 'tests.test_current_source_reader.CurrentSourceReaderTest.test_evidence_manifest_mutation_refuses', 'tests.test_public_proof_portability.PublicProofPortabilityTest.test_immutable_original_proof_bundle', 'tests.test_public_proof_portability.PublicProofPortabilityTest.test_manifest_tamper_and_raw_record_tamper_refuse', 'tests.test_public_proof_portability.PublicProofPortabilityTest.test_unknown_private_history_and_snapshot_tamper_refuse'])

    def test_ls05_p6_s01_negative_current_proof_controls(self):
        self.check(['tests.test_current_format_acceptance.CurrentFormatAcceptanceTest.test_ls05_p6_s01_negative_current', 'tests.test_current_source_reader.CurrentSourceReaderTest.test_changed_current_input_invalidates_route_cache'])

    def test_ls05_p5_s01_negative_current_proof_controls(self):
        self.check(['tests.test_current_format_acceptance.CurrentFormatAcceptanceTest.test_ls05_p5_s01_negative', 'tests.test_current_source_reader.CurrentSourceReaderTest.test_current_owner_mutation_refuses', 'tests.test_current_source_reader.CurrentSourceReaderTest.test_historical_input_mutation_refuses'])

    def test_vc19_p1_c08_positive_current_retained_alias(self):
        self.check(['tests.test_current_feed_authority_whole.CurrentFeedAuthorityWholeTest.test_exact_union_and_final_root_reread_for_current_and_recovery'])

    def test_vc19_p2_c04_negative_current_retained_alias(self):
        self.check(['tests.test_current_feed_authority_whole.CurrentFeedAuthorityWholeTest.test_repinned_role_point_and_catalog_grammar_refused_before_persistence'])

    def test_vc19_p2_c05_negative_current_retained_alias(self):
        self.check(['tests.test_current_feed_authority_whole.CurrentFeedAuthorityWholeTest.test_repinned_role_point_and_catalog_grammar_refused_before_persistence'])

    def test_vc19_p3_c05_negative_current_retained_alias(self):
        self.check(['tests.test_current_feed_authority_whole.CurrentFeedAuthorityWholeTest.test_prepare_refuses_bad_profile_envelope_age_and_missing_closure_atomically'])

    def test_vc19_p3_c06_negative_current_retained_alias(self):
        self.check(['tests.test_current_feed_authority_whole.CurrentFeedAuthorityWholeTest.test_prepare_refuses_bad_profile_envelope_age_and_missing_closure_atomically'])

    def test_vc19_p3_c12_negative_current_retained_alias(self):
        self.check(['tests.test_current_feed_authority_whole.CurrentFeedAuthorityWholeTest.test_prepare_refuses_bad_profile_envelope_age_and_missing_closure_atomically'])

    def test_vc20_p1_c04_negative_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c02_negative_current'])

    def test_vc20_p1_c05_positive_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c03_positive_current'])

    def test_vc20_p1_c06_positive_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c03_positive_current'])

    def test_vc20_p1_c06_negative_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c02_negative_current'])

    def test_vc20_p1_c07_negative_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c02_negative_current'])

    def test_vc20_p1_motionwhole_positive_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c03_positive_current'])

    def test_vc20_p1_motionwhole_negative_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c02_negative_current'])

    def test_vc20_p2_motionwhole_positive_current_retained_alias(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p2_source_update_positive'])

    def test_vc20_p2_motionwhole_negative_current_retained_alias(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p2_lifecycle_negative'])

    def test_vc20_p3_motionwhole_positive_current_retained_alias(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p3_recovery_positive'])

    def test_vc20_p3_motionwhole_negative_current_retained_alias(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p3_refusal_negative'])

    def test_vc20_p3_motionwhole_hosthttp_negative_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p3_motionwhole_hostclosure_negative_current'])

    def test_vc20_p1_motionwhole_sdkpixels_positive_current_retained_alias(self):
        self.check(['tests.test_public_case_mappings.PublicMappedCases.test_vc20_p1_c03_positive_current'])

    def test_vc20_p3_motionwhole_sdkcleanup_negative_current_retained_alias(self):
        self.check(['tests.test_current_native_scene_whole.CurrentNativeSceneWhole.test_p3_refusal_negative'])
