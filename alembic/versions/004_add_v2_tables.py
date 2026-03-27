"""Add v2 schema tables: members, self-review, scheduling, accountability, analytics

Revision ID: 004
Revises: 003
Create Date: 2026-03-28

Adds all new tables required by the v2.0 roadmap without modifying existing
tables. Existing functionality is fully backward-compatible.

New tables:
  - project_members          (persona-based team membership)
  - recurring_review_schedules (scheduled recurring reviews)
  - milestone_review_triggers  (event-triggered reviews)
  - review_instances           (concrete occurrences of a scheduled review)
  - self_review_sessions       (persona-based self-review before stakeholder meeting)
  - consolidated_self_review_reports (aggregated self-review result)
  - reminder_queue             (automated reminder scheduling)
  - meeting_blocks             (block meetings until self-review complete)
  - stakeholder_preparation    (prep pack tracking per stakeholder)
  - gap_tracking               (cross-review gap persistence)
  - review_trend_analytics     (aggregated trend data per project)
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── project_members ───────────────────────────────────────────────────────
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('persona', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('joined_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'user_id', 'persona', name='uq_project_member_persona'),
    )
    op.create_index('idx_project_members_project', 'project_members', ['project_id'])
    op.create_index('idx_project_members_user',    'project_members', ['user_id'])
    op.create_index('idx_project_members_persona', 'project_members', ['persona'])

    # ── recurring_review_schedules ────────────────────────────────────────────
    op.create_table(
        'recurring_review_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('cadence', sa.String(50), nullable=False),   # daily|weekly|biweekly|monthly|quarterly
        sa.Column('day_of_week', sa.Integer(), nullable=True), # 0=Mon for weekly cadences
        sa.Column('time_of_day', sa.String(5), nullable=True), # HH:MM
        sa.Column('phase', sa.String(50), nullable=True),      # planning|execution|pre_launch|post_launch
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_recurring_schedules_project', 'recurring_review_schedules', ['project_id'])

    # ── milestone_review_triggers ─────────────────────────────────────────────
    op.create_table(
        'milestone_review_triggers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=True),
        sa.Column('trigger_event', sa.String(100), nullable=False), # sprint_review|pre_release|go_no_go|post_incident
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='1', nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_milestone_triggers_project', 'milestone_review_triggers', ['project_id'])

    # ── review_instances ──────────────────────────────────────────────────────
    op.create_table(
        'review_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=True),
        sa.Column('trigger_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('review_type', sa.String(50), nullable=False),  # scheduled|milestone|ad_hoc
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('self_review_due_at', sa.DateTime(), nullable=True),
        sa.Column('self_review_required', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        # pending|self_review_in_progress|self_review_complete|stakeholder_meeting|completed|blocked
        sa.Column('readiness_score', sa.Float(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schedule_id'], ['recurring_review_schedules.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['trigger_id'], ['milestone_review_triggers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_review_instances_project',   'review_instances', ['project_id'])
    op.create_index('idx_review_instances_status',    'review_instances', ['status'])
    op.create_index('idx_review_instances_scheduled', 'review_instances', ['scheduled_at'])

    # ── self_review_sessions ──────────────────────────────────────────────────
    op.create_table(
        'self_review_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_instance_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('checklist_id', sa.Integer(), nullable=True),
        sa.Column('persona', sa.String(100), nullable=True),
        # pm|tech_lead|devops|qa|security|product_owner
        sa.Column('participant_id', sa.Integer(), nullable=True),
        sa.Column('session_type', sa.String(50), server_default='self', nullable=False),
        # self|persona|consolidated
        sa.Column('readiness_score', sa.Float(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        # pending|in_progress|completed|skipped
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['review_instance_id'], ['review_instances.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['checklist_id'], ['checklists.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['participant_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_self_review_instance',  'self_review_sessions', ['review_instance_id'])
    op.create_index('idx_self_review_project',   'self_review_sessions', ['project_id'])
    op.create_index('idx_self_review_participant','self_review_sessions', ['participant_id'])
    op.create_index('idx_self_review_status',    'self_review_sessions', ['status'])

    # ── consolidated_self_review_reports ──────────────────────────────────────
    op.create_table(
        'consolidated_self_review_reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_instance_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('overall_readiness_score', sa.Float(), nullable=True),
        sa.Column('persona_scores', sa.JSON(), nullable=True),
        sa.Column('cross_persona_gaps', sa.JSON(), nullable=True),  # list of gap descriptions
        sa.Column('recommended_focus_areas', sa.JSON(), nullable=True),
        sa.Column('generated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('generated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['review_instance_id'], ['review_instances.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_consolidated_reports_instance', 'consolidated_self_review_reports', ['review_instance_id'])
    op.create_index('idx_consolidated_reports_project',  'consolidated_self_review_reports', ['project_id'])

    # ── reminder_queue ────────────────────────────────────────────────────────
    op.create_table(
        'reminder_queue',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_instance_id', sa.Integer(), nullable=True),
        sa.Column('reminder_type', sa.String(50), nullable=False),
        # t_minus_7|t_minus_3|t_minus_2|t_minus_1|t_zero|escalation
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending', nullable=False),
        # pending|sent|failed|cancelled
        sa.Column('recipient_ids', sa.JSON(), nullable=True),
        sa.Column('template_name', sa.String(100), nullable=True),
        sa.Column('retry_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['review_instance_id'], ['review_instances.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_reminder_queue_scheduled', 'reminder_queue', ['scheduled_at'])
    op.create_index('idx_reminder_queue_status',    'reminder_queue', ['status'])

    # ── meeting_blocks ────────────────────────────────────────────────────────
    op.create_table(
        'meeting_blocks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_instance_id', sa.Integer(), nullable=True),
        sa.Column('reason', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), server_default='active', nullable=False),
        # active|lifted|exception_approved
        sa.Column('blocked_by', sa.Integer(), nullable=True),
        sa.Column('unblocked_by', sa.Integer(), nullable=True),
        sa.Column('override_approved_by', sa.Integer(), nullable=True),
        sa.Column('exception_reason', sa.Text(), nullable=True),
        sa.Column('blocked_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('unblocked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['review_instance_id'], ['review_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['blocked_by'], ['users.id']),
        sa.ForeignKeyConstraint(['unblocked_by'], ['users.id']),
        sa.ForeignKeyConstraint(['override_approved_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_meeting_blocks_instance', 'meeting_blocks', ['review_instance_id'])
    op.create_index('idx_meeting_blocks_status',   'meeting_blocks', ['status'])

    # ── stakeholder_preparation ───────────────────────────────────────────────
    op.create_table(
        'stakeholder_preparation',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('review_instance_id', sa.Integer(), nullable=True),
        sa.Column('stakeholder_id', sa.Integer(), nullable=False),
        sa.Column('preparation_pack_sent_at', sa.DateTime(), nullable=True),
        sa.Column('preparation_pack_viewed_at', sa.DateTime(), nullable=True),
        sa.Column('readiness_score_viewed', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('suggested_questions_viewed', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('acknowledged', sa.Boolean(), server_default='0', nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['review_instance_id'], ['review_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stakeholder_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_stakeholder_prep_instance',    'stakeholder_preparation', ['review_instance_id'])
    op.create_index('idx_stakeholder_prep_stakeholder', 'stakeholder_preparation', ['stakeholder_id'])

    # ── gap_tracking ──────────────────────────────────────────────────────────
    op.create_table(
        'gap_tracking',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('checklist_item_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('first_identified_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('gap_description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(50), nullable=True),   # low|medium|high|critical
        sa.Column('status', sa.String(50), server_default='open', nullable=False),
        # open|in_progress|resolved|accepted_risk
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('appeared_in_review_count', sa.Integer(), server_default='1', nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['checklist_item_id'], ['checklist_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_gap_tracking_project', 'gap_tracking', ['project_id'])
    op.create_index('idx_gap_tracking_status',  'gap_tracking', ['status'])
    op.create_index('idx_gap_tracking_item',    'gap_tracking', ['checklist_item_id'])

    # ── review_trend_analytics ────────────────────────────────────────────────
    op.create_table(
        'review_trend_analytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(), nullable=False),
        sa.Column('period_end', sa.DateTime(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),   # weekly|monthly|quarterly
        sa.Column('total_reviews', sa.Integer(), server_default='0', nullable=False),
        sa.Column('avg_compliance_score', sa.Float(), nullable=True),
        sa.Column('avg_readiness_score', sa.Float(), nullable=True),
        sa.Column('self_review_completion_rate', sa.Float(), nullable=True),  # 0-1
        sa.Column('on_time_completion_rate', sa.Float(), nullable=True),      # 0-1
        sa.Column('meeting_block_rate', sa.Float(), nullable=True),           # 0-1
        sa.Column('persistent_gaps', sa.JSON(), nullable=True),               # list of gap descriptions
        sa.Column('top_failing_areas', sa.JSON(), nullable=True),             # list of area names
        sa.Column('computed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'period_start', 'period_type', name='uq_trend_period'),
    )
    op.create_index('idx_trend_analytics_project', 'review_trend_analytics', ['project_id'])
    op.create_index('idx_trend_analytics_period',  'review_trend_analytics', ['period_start'])


def downgrade() -> None:
    op.drop_table('review_trend_analytics')
    op.drop_table('gap_tracking')
    op.drop_table('stakeholder_preparation')
    op.drop_table('meeting_blocks')
    op.drop_table('reminder_queue')
    op.drop_table('consolidated_self_review_reports')
    op.drop_table('self_review_sessions')
    op.drop_table('review_instances')
    op.drop_table('milestone_review_triggers')
    op.drop_table('recurring_review_schedules')
    op.drop_table('project_members')
