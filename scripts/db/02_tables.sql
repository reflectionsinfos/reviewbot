CREATE SEQUENCE public.autonomous_review_jobs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.autonomous_review_overrides_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.autonomous_review_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.checklist_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.checklist_recommendations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.checklist_routing_rules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.checklists_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.consolidated_self_review_reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.gap_tracking_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.meeting_blocks_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.milestone_review_triggers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.project_members_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.recurring_review_schedules_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.reminder_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.report_approvals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.review_instances_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.review_responses_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.review_trend_analytics_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.reviews_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.self_review_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.stakeholder_preparation_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE public.autonomous_review_jobs (
    id integer NOT NULL,
    project_id integer NOT NULL,
    checklist_id integer NOT NULL,
    source_path character varying NOT NULL,
    status character varying,
    total_items integer,
    completed_items integer,
    error_message text,
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_at timestamp without time zone,
    created_by integer,
    agent_metadata jsonb,
    green_count integer DEFAULT 0,
    amber_count integer DEFAULT 0,
    red_count integer DEFAULT 0,
    skipped_count integer DEFAULT 0,
    na_count integer DEFAULT 0,
    compliance_score double precision DEFAULT 0.0
);

CREATE TABLE public.autonomous_review_overrides (
    id integer NOT NULL,
    result_id integer NOT NULL,
    new_rag_status character varying NOT NULL,
    comments text NOT NULL,
    reason character varying,
    overridden_by integer NOT NULL,
    overridden_at timestamp without time zone NOT NULL
);

CREATE TABLE public.autonomous_review_results (
    id integer NOT NULL,
    job_id integer NOT NULL,
    checklist_item_id integer NOT NULL,
    strategy character varying,
    rag_status character varying,
    evidence text,
    confidence double precision,
    files_checked json,
    skip_reason text,
    evidence_hint text,
    created_at timestamp without time zone,
    needs_human_sign_off boolean DEFAULT false NOT NULL
);

CREATE TABLE public.checklist_items (
    id integer NOT NULL,
    checklist_id integer NOT NULL,
    item_code character varying,
    area character varying,
    question text NOT NULL,
    category character varying,
    weight double precision,
    expected_evidence text,
    suggested_for_domains json,
    "order" integer,
    created_at timestamp without time zone,
    is_review_mandatory boolean DEFAULT true NOT NULL
);

CREATE TABLE public.checklist_recommendations (
    id integer NOT NULL,
    checklist_id integer NOT NULL,
    suggestion_type character varying,
    description text,
    rationale text,
    priority character varying,
    based_on_domain character varying,
    confidence_score double precision,
    status character varying,
    reviewed_by integer,
    created_at timestamp without time zone
);

CREATE TABLE public.checklist_routing_rules (
    id integer NOT NULL,
    checklist_item_id integer,
    checklist_id integer,
    strategy character varying(50) NOT NULL,
    skip_reason text,
    evidence_hint text,
    created_by_id integer,
    created_at timestamp without time zone,
    is_active boolean
);

CREATE TABLE public.checklists (
    id integer NOT NULL,
    name character varying NOT NULL,
    type character varying NOT NULL,
    version character varying,
    project_id integer,
    is_global boolean,
    created_at timestamp without time zone,
    updated_at timestamp without time zone,
    source_checklist_id integer,
    area_codes jsonb
);

CREATE TABLE public.consolidated_self_review_reports (
    id integer NOT NULL,
    review_instance_id integer,
    project_id integer NOT NULL,
    overall_readiness_score double precision,
    persona_scores json,
    cross_persona_gaps json,
    recommended_focus_areas json,
    generated_at timestamp without time zone,
    generated_by integer
);

CREATE TABLE public.gap_tracking (
    id integer NOT NULL,
    checklist_item_id integer,
    project_id integer NOT NULL,
    first_identified_at timestamp without time zone,
    gap_description text,
    severity character varying(50),
    status character varying(50),
    owner_id integer,
    appeared_in_review_count integer,
    last_seen_at timestamp without time zone,
    resolved_at timestamp without time zone
);

CREATE TABLE public.meeting_blocks (
    id integer NOT NULL,
    review_instance_id integer,
    reason character varying(255) NOT NULL,
    status character varying(50),
    blocked_by integer,
    unblocked_by integer,
    override_approved_by integer,
    exception_reason text,
    blocked_at timestamp without time zone,
    unblocked_at timestamp without time zone
);

CREATE TABLE public.milestone_review_triggers (
    id integer NOT NULL,
    project_id integer NOT NULL,
    checklist_id integer,
    trigger_event character varying(100) NOT NULL,
    description text,
    is_active boolean,
    created_by integer,
    created_at timestamp without time zone
);

CREATE TABLE public.project_members (
    id integer NOT NULL,
    project_id integer NOT NULL,
    user_id integer NOT NULL,
    persona character varying(100),
    is_active boolean,
    joined_at timestamp without time zone
);

CREATE TABLE public.projects (
    id integer NOT NULL,
    name character varying NOT NULL,
    domain character varying,
    description text,
    tech_stack json,
    stakeholders json,
    start_date timestamp without time zone,
    end_date timestamp without time zone,
    status character varying,
    owner_id integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE TABLE public.recurring_review_schedules (
    id integer NOT NULL,
    project_id integer NOT NULL,
    checklist_id integer,
    name character varying(255) NOT NULL,
    cadence character varying(50) NOT NULL,
    day_of_week integer,
    time_of_day character varying(5),
    phase character varying(50),
    is_active boolean,
    created_by integer,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE TABLE public.reminder_queue (
    id integer NOT NULL,
    review_instance_id integer,
    reminder_type character varying(50) NOT NULL,
    scheduled_at timestamp without time zone NOT NULL,
    sent_at timestamp without time zone,
    status character varying(50),
    recipient_ids json,
    template_name character varying(100),
    retry_count integer,
    last_error text,
    created_at timestamp without time zone
);

CREATE TABLE public.report_approvals (
    id integer NOT NULL,
    report_id integer NOT NULL,
    approver_id integer NOT NULL,
    status character varying,
    comments text,
    decided_at timestamp without time zone,
    created_at timestamp without time zone
);

CREATE TABLE public.reports (
    id integer NOT NULL,
    review_id integer NOT NULL,
    summary text,
    overall_rag_status character varying,
    compliance_score double precision,
    areas_followed json,
    gaps_identified json,
    recommendations json,
    action_items json,
    pdf_path character varying,
    markdown_path character varying,
    approval_status character varying,
    requires_approval boolean,
    created_at timestamp without time zone,
    approved_at timestamp without time zone,
    autonomous_review_job_id integer
);

CREATE TABLE public.review_instances (
    id integer NOT NULL,
    project_id integer NOT NULL,
    schedule_id integer,
    trigger_id integer,
    title character varying(255) NOT NULL,
    review_type character varying(50) NOT NULL,
    scheduled_at timestamp without time zone NOT NULL,
    self_review_due_at timestamp without time zone,
    self_review_required boolean,
    status character varying(50),
    readiness_score double precision,
    created_by integer,
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);

CREATE TABLE public.review_responses (
    id integer NOT NULL,
    review_id integer NOT NULL,
    checklist_item_id integer NOT NULL,
    answer character varying,
    comments text,
    rag_status character varying,
    evidence_links json,
    attachments json,
    voice_recording_path character varying,
    transcript text,
    created_at timestamp without time zone,
    updated_at timestamp without time zone
);

CREATE TABLE public.review_trend_analytics (
    id integer NOT NULL,
    project_id integer NOT NULL,
    period_start timestamp without time zone NOT NULL,
    period_end timestamp without time zone NOT NULL,
    period_type character varying(20) NOT NULL,
    total_reviews integer,
    avg_compliance_score double precision,
    avg_readiness_score double precision,
    self_review_completion_rate double precision,
    on_time_completion_rate double precision,
    meeting_block_rate double precision,
    persistent_gaps json,
    top_failing_areas json,
    computed_at timestamp without time zone
);

CREATE TABLE public.reviews (
    id integer NOT NULL,
    project_id integer NOT NULL,
    checklist_id integer NOT NULL,
    title character varying,
    conducted_by integer,
    participants json,
    review_date timestamp without time zone,
    status character varying,
    voice_enabled boolean,
    notes text,
    created_at timestamp without time zone,
    completed_at timestamp without time zone
);

CREATE TABLE public.self_review_sessions (
    id integer NOT NULL,
    review_instance_id integer,
    project_id integer NOT NULL,
    checklist_id integer,
    persona character varying(100),
    participant_id integer,
    session_type character varying(50),
    readiness_score double precision,
    status character varying(50),
    started_at timestamp without time zone,
    completed_at timestamp without time zone,
    created_at timestamp without time zone
);

CREATE TABLE public.stakeholder_preparation (
    id integer NOT NULL,
    review_instance_id integer,
    stakeholder_id integer NOT NULL,
    preparation_pack_sent_at timestamp without time zone,
    preparation_pack_viewed_at timestamp without time zone,
    readiness_score_viewed boolean,
    suggested_questions_viewed boolean,
    acknowledged boolean,
    acknowledged_at timestamp without time zone,
    created_at timestamp without time zone
);

CREATE TABLE public.users (
    id integer NOT NULL,
    email character varying NOT NULL,
    full_name character varying NOT NULL,
    hashed_password character varying NOT NULL,
    role character varying,
    is_active boolean,
    created_at timestamp without time zone
);

ALTER SEQUENCE public.autonomous_review_jobs_id_seq OWNED BY public.autonomous_review_jobs.id;
ALTER SEQUENCE public.autonomous_review_overrides_id_seq OWNED BY public.autonomous_review_overrides.id;
ALTER SEQUENCE public.autonomous_review_results_id_seq OWNED BY public.autonomous_review_results.id;
ALTER SEQUENCE public.checklist_items_id_seq OWNED BY public.checklist_items.id;
ALTER SEQUENCE public.checklist_recommendations_id_seq OWNED BY public.checklist_recommendations.id;
ALTER SEQUENCE public.checklist_routing_rules_id_seq OWNED BY public.checklist_routing_rules.id;
ALTER SEQUENCE public.checklists_id_seq OWNED BY public.checklists.id;
ALTER SEQUENCE public.consolidated_self_review_reports_id_seq OWNED BY public.consolidated_self_review_reports.id;
ALTER SEQUENCE public.gap_tracking_id_seq OWNED BY public.gap_tracking.id;
ALTER SEQUENCE public.meeting_blocks_id_seq OWNED BY public.meeting_blocks.id;
ALTER SEQUENCE public.milestone_review_triggers_id_seq OWNED BY public.milestone_review_triggers.id;
ALTER SEQUENCE public.project_members_id_seq OWNED BY public.project_members.id;
ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;
ALTER SEQUENCE public.recurring_review_schedules_id_seq OWNED BY public.recurring_review_schedules.id;
ALTER SEQUENCE public.reminder_queue_id_seq OWNED BY public.reminder_queue.id;
ALTER SEQUENCE public.report_approvals_id_seq OWNED BY public.report_approvals.id;
ALTER SEQUENCE public.reports_id_seq OWNED BY public.reports.id;
ALTER SEQUENCE public.review_instances_id_seq OWNED BY public.review_instances.id;
ALTER SEQUENCE public.review_responses_id_seq OWNED BY public.review_responses.id;
ALTER SEQUENCE public.review_trend_analytics_id_seq OWNED BY public.review_trend_analytics.id;
ALTER SEQUENCE public.reviews_id_seq OWNED BY public.reviews.id;
ALTER SEQUENCE public.self_review_sessions_id_seq OWNED BY public.self_review_sessions.id;
ALTER SEQUENCE public.stakeholder_preparation_id_seq OWNED BY public.stakeholder_preparation.id;
ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;
