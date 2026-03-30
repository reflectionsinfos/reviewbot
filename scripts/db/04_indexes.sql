CREATE INDEX ix_autonomous_review_jobs_id ON public.autonomous_review_jobs USING btree (id);

CREATE INDEX ix_autonomous_review_overrides_id ON public.autonomous_review_overrides USING btree (id);

CREATE INDEX ix_autonomous_review_results_id ON public.autonomous_review_results USING btree (id);

CREATE INDEX ix_checklist_items_id ON public.checklist_items USING btree (id);

CREATE INDEX ix_checklist_recommendations_id ON public.checklist_recommendations USING btree (id);

CREATE INDEX ix_checklist_routing_rules_checklist_id ON public.checklist_routing_rules USING btree (checklist_id);

CREATE INDEX ix_checklist_routing_rules_checklist_item_id ON public.checklist_routing_rules USING btree (checklist_item_id);

CREATE INDEX ix_checklist_routing_rules_id ON public.checklist_routing_rules USING btree (id);

CREATE INDEX ix_checklists_id ON public.checklists USING btree (id);

CREATE INDEX ix_consolidated_self_review_reports_id ON public.consolidated_self_review_reports USING btree (id);

CREATE INDEX ix_gap_tracking_id ON public.gap_tracking USING btree (id);

CREATE INDEX ix_meeting_blocks_id ON public.meeting_blocks USING btree (id);

CREATE INDEX ix_milestone_review_triggers_id ON public.milestone_review_triggers USING btree (id);

CREATE INDEX ix_project_members_id ON public.project_members USING btree (id);

CREATE INDEX ix_projects_id ON public.projects USING btree (id);

CREATE INDEX ix_recurring_review_schedules_id ON public.recurring_review_schedules USING btree (id);

CREATE INDEX ix_reminder_queue_id ON public.reminder_queue USING btree (id);

CREATE INDEX ix_report_approvals_id ON public.report_approvals USING btree (id);

CREATE INDEX ix_reports_id ON public.reports USING btree (id);

CREATE INDEX ix_review_instances_id ON public.review_instances USING btree (id);

CREATE INDEX ix_review_responses_id ON public.review_responses USING btree (id);

CREATE INDEX ix_review_trend_analytics_id ON public.review_trend_analytics USING btree (id);

CREATE INDEX ix_reviews_id ON public.reviews USING btree (id);

CREATE INDEX ix_self_review_sessions_id ON public.self_review_sessions USING btree (id);

CREATE INDEX ix_stakeholder_preparation_id ON public.stakeholder_preparation USING btree (id);

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);

CREATE INDEX ix_users_id ON public.users USING btree (id);
