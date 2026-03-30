ALTER TABLE ONLY public.autonomous_review_jobs
    ADD CONSTRAINT autonomous_review_jobs_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.autonomous_review_overrides
    ADD CONSTRAINT autonomous_review_overrides_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.autonomous_review_results
    ADD CONSTRAINT autonomous_review_results_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.checklist_recommendations
    ADD CONSTRAINT checklist_recommendations_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.checklist_routing_rules
    ADD CONSTRAINT checklist_routing_rules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.checklists
    ADD CONSTRAINT checklists_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.consolidated_self_review_reports
    ADD CONSTRAINT consolidated_self_review_reports_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.gap_tracking
    ADD CONSTRAINT gap_tracking_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.meeting_blocks
    ADD CONSTRAINT meeting_blocks_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.milestone_review_triggers
    ADD CONSTRAINT milestone_review_triggers_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.recurring_review_schedules
    ADD CONSTRAINT recurring_review_schedules_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.reminder_queue
    ADD CONSTRAINT reminder_queue_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.report_approvals
    ADD CONSTRAINT report_approvals_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_review_id_key UNIQUE (review_id);

ALTER TABLE ONLY public.review_instances
    ADD CONSTRAINT review_instances_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.review_responses
    ADD CONSTRAINT review_responses_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.review_trend_analytics
    ADD CONSTRAINT review_trend_analytics_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.self_review_sessions
    ADD CONSTRAINT self_review_sessions_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.stakeholder_preparation
    ADD CONSTRAINT stakeholder_preparation_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);

ALTER TABLE ONLY public.autonomous_review_jobs
    ADD CONSTRAINT autonomous_review_jobs_checklist_id_fkey FOREIGN KEY (checklist_id) REFERENCES public.checklists(id);

ALTER TABLE ONLY public.autonomous_review_jobs
    ADD CONSTRAINT autonomous_review_jobs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.autonomous_review_jobs
    ADD CONSTRAINT autonomous_review_jobs_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);

ALTER TABLE ONLY public.autonomous_review_overrides
    ADD CONSTRAINT autonomous_review_overrides_overridden_by_fkey FOREIGN KEY (overridden_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.autonomous_review_overrides
    ADD CONSTRAINT autonomous_review_overrides_result_id_fkey FOREIGN KEY (result_id) REFERENCES public.autonomous_review_results(id);

ALTER TABLE ONLY public.autonomous_review_results
    ADD CONSTRAINT autonomous_review_results_checklist_item_id_fkey FOREIGN KEY (checklist_item_id) REFERENCES public.checklist_items(id);

ALTER TABLE ONLY public.autonomous_review_results
    ADD CONSTRAINT autonomous_review_results_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.autonomous_review_jobs(id);

ALTER TABLE ONLY public.checklist_items
    ADD CONSTRAINT checklist_items_checklist_id_fkey FOREIGN KEY (checklist_id) REFERENCES public.checklists(id);

ALTER TABLE ONLY public.checklist_recommendations
    ADD CONSTRAINT checklist_recommendations_checklist_id_fkey FOREIGN KEY (checklist_id) REFERENCES public.checklists(id);

ALTER TABLE ONLY public.checklist_recommendations
    ADD CONSTRAINT checklist_recommendations_reviewed_by_fkey FOREIGN KEY (reviewed_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.checklist_routing_rules
    ADD CONSTRAINT checklist_routing_rules_checklist_id_fkey FOREIGN KEY (checklist_id) REFERENCES public.checklists(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.checklist_routing_rules
    ADD CONSTRAINT checklist_routing_rules_checklist_item_id_fkey FOREIGN KEY (checklist_item_id) REFERENCES public.checklist_items(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.checklist_routing_rules
    ADD CONSTRAINT checklist_routing_rules_created_by_id_fkey FOREIGN KEY (created_by_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.checklists
    ADD CONSTRAINT checklists_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);

ALTER TABLE ONLY public.consolidated_self_review_reports
    ADD CONSTRAINT consolidated_self_review_reports_generated_by_fkey FOREIGN KEY (generated_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.consolidated_self_review_reports
    ADD CONSTRAINT consolidated_self_review_reports_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.gap_tracking
    ADD CONSTRAINT gap_tracking_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.gap_tracking
    ADD CONSTRAINT gap_tracking_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.meeting_blocks
    ADD CONSTRAINT meeting_blocks_blocked_by_fkey FOREIGN KEY (blocked_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.meeting_blocks
    ADD CONSTRAINT meeting_blocks_override_approved_by_fkey FOREIGN KEY (override_approved_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.meeting_blocks
    ADD CONSTRAINT meeting_blocks_review_instance_id_fkey FOREIGN KEY (review_instance_id) REFERENCES public.review_instances(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.meeting_blocks
    ADD CONSTRAINT meeting_blocks_unblocked_by_fkey FOREIGN KEY (unblocked_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.milestone_review_triggers
    ADD CONSTRAINT milestone_review_triggers_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.milestone_review_triggers
    ADD CONSTRAINT milestone_review_triggers_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.project_members
    ADD CONSTRAINT project_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.recurring_review_schedules
    ADD CONSTRAINT recurring_review_schedules_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.recurring_review_schedules
    ADD CONSTRAINT recurring_review_schedules_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reminder_queue
    ADD CONSTRAINT reminder_queue_review_instance_id_fkey FOREIGN KEY (review_instance_id) REFERENCES public.review_instances(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.report_approvals
    ADD CONSTRAINT report_approvals_approver_id_fkey FOREIGN KEY (approver_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.report_approvals
    ADD CONSTRAINT report_approvals_report_id_fkey FOREIGN KEY (report_id) REFERENCES public.reports(id);

ALTER TABLE ONLY public.reports
    ADD CONSTRAINT reports_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.reviews(id);

ALTER TABLE ONLY public.review_instances
    ADD CONSTRAINT review_instances_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.review_instances
    ADD CONSTRAINT review_instances_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.review_responses
    ADD CONSTRAINT review_responses_checklist_item_id_fkey FOREIGN KEY (checklist_item_id) REFERENCES public.checklist_items(id);

ALTER TABLE ONLY public.review_responses
    ADD CONSTRAINT review_responses_review_id_fkey FOREIGN KEY (review_id) REFERENCES public.reviews(id);

ALTER TABLE ONLY public.review_trend_analytics
    ADD CONSTRAINT review_trend_analytics_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_checklist_id_fkey FOREIGN KEY (checklist_id) REFERENCES public.checklists(id);

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_conducted_by_fkey FOREIGN KEY (conducted_by) REFERENCES public.users(id);

ALTER TABLE ONLY public.reviews
    ADD CONSTRAINT reviews_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);

ALTER TABLE ONLY public.self_review_sessions
    ADD CONSTRAINT self_review_sessions_participant_id_fkey FOREIGN KEY (participant_id) REFERENCES public.users(id);

ALTER TABLE ONLY public.self_review_sessions
    ADD CONSTRAINT self_review_sessions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.stakeholder_preparation
    ADD CONSTRAINT stakeholder_preparation_review_instance_id_fkey FOREIGN KEY (review_instance_id) REFERENCES public.review_instances(id) ON DELETE CASCADE;

ALTER TABLE ONLY public.stakeholder_preparation
    ADD CONSTRAINT stakeholder_preparation_stakeholder_id_fkey FOREIGN KEY (stakeholder_id) REFERENCES public.users(id);
