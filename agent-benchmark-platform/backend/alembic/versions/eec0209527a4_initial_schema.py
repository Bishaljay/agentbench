"""initial_schema

Revision ID: eec0209527a4
Revises: 
Create Date: 2026-11-09 21:46:10.574697

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'eec0209527a4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return insp.has_table(table_name)

def get_columns(table_name: str) -> set:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return {col['name'] for col in insp.get_columns(table_name)}

def upgrade() -> None:
    # 1. agents
    if not table_exists('agents'):
        op.create_table('agents',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('kind', sa.String(length=50), nullable=False),
            sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
            sa.Column('capabilities', sa.Text(), nullable=False, server_default='deterministic'),
            sa.Column('description', sa.Text(), nullable=False, server_default=''),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('agents', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_agents_name'), ['name'], unique=True)
    else:
        cols = get_columns('agents')
        with op.batch_alter_table('agents', schema=None) as batch_op:
            if 'description' not in cols:
                batch_op.add_column(sa.Column('description', sa.Text(), nullable=False, server_default=''))
            if 'created_at' not in cols:
                batch_op.add_column(sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''))

    # 2. benchmarks
    if not table_exists('benchmarks'):
        op.create_table('benchmarks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False, server_default=''),
            sa.Column('category', sa.String(length=50), nullable=False, server_default='General'),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('benchmarks', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_benchmarks_name'), ['name'], unique=True)
    else:
        cols = get_columns('benchmarks')
        with op.batch_alter_table('benchmarks', schema=None) as batch_op:
            if 'created_at' not in cols:
                batch_op.add_column(sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''))

    # 3. roles
    if not table_exists('roles'):
        op.create_table('roles',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=False, server_default=''),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('roles', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_roles_name'), ['name'], unique=True)

    # 4. system_settings
    if not table_exists('system_settings'):
        op.create_table('system_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('key', sa.String(length=100), nullable=False),
            sa.Column('value', sa.Text(), nullable=False),
            sa.Column('description', sa.String(length=255), nullable=False, server_default=''),
            sa.Column('updated_at', sa.String(length=64), nullable=False, server_default=''),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('system_settings', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_system_settings_key'), ['key'], unique=True)

    # 5. users
    if not table_exists('users'):
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=80), nullable=False),
            sa.Column('password', sa.String(length=255), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=50), nullable=False, server_default='operator'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('users', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)
    else:
        cols = get_columns('users')
        with op.batch_alter_table('users', schema=None) as batch_op:
            if 'role' not in cols:
                batch_op.add_column(sa.Column('role', sa.String(length=50), nullable=False, server_default='operator'))
            if 'is_active' not in cols:
                batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
            if 'created_at' not in cols:
                batch_op.add_column(sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''))

    # 6. agent_capabilities
    if not table_exists('agent_capabilities'):
        op.create_table('agent_capabilities',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('agent_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('description', sa.Text(), nullable=False, server_default=''),
            sa.Column('parameters', sa.Text(), nullable=False, server_default='{}'),
            sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 7. agent_versions
    if not table_exists('agent_versions'):
        op.create_table('agent_versions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('agent_id', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(length=50), nullable=False),
            sa.Column('code_hash', sa.String(length=64), nullable=True),
            sa.Column('changelog', sa.Text(), nullable=False, server_default=''),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 8. audit_logs
    if not table_exists('audit_logs'):
        op.create_table('audit_logs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('username', sa.String(length=80), nullable=False, server_default='system'),
            sa.Column('action', sa.String(length=100), nullable=False),
            sa.Column('entity_type', sa.String(length=50), nullable=False),
            sa.Column('entity_id', sa.String(length=50), nullable=True),
            sa.Column('details', sa.Text(), nullable=False, server_default='{}'),
            sa.Column('ip_address', sa.String(length=50), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('audit_logs', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_audit_logs_action'), ['action'], unique=False)
            batch_op.create_index(batch_op.f('ix_audit_logs_user_id'), ['user_id'], unique=False)

    # 9. benchmark_runs
    if not table_exists('benchmark_runs'):
        op.create_table('benchmark_runs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('agent_id', sa.Integer(), nullable=False),
            sa.Column('benchmark_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False, server_default='QUEUED'),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.Column('finished_at', sa.String(length=64), nullable=True),
            sa.Column('cancel', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['benchmark_id'], ['benchmarks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('benchmark_runs', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_benchmark_runs_agent_id'), ['agent_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_benchmark_runs_benchmark_id'), ['benchmark_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_benchmark_runs_status'), ['status'], unique=False)

    # 10. benchmark_versions
    if not table_exists('benchmark_versions'):
        op.create_table('benchmark_versions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('benchmark_id', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
            sa.Column('notes', sa.Text(), nullable=False, server_default=''),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['benchmark_id'], ['benchmarks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 11. notifications
    if not table_exists('notifications'):
        op.create_table('notifications',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('type', sa.String(length=50), nullable=False, server_default='info'),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('notifications', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_notifications_user_id'), ['user_id'], unique=False)

    # 12. session_tokens
    if not table_exists('session_tokens'):
        op.create_table('session_tokens',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('token', sa.String(length=255), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('expires_at', sa.String(length=64), nullable=False),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.Column('is_revoked', sa.Boolean(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('session_tokens', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_session_tokens_token'), ['token'], unique=True)

    # 13. tasks
    if not table_exists('tasks'):
        op.create_table('tasks',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('benchmark_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=150), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False, server_default='General'),
            sa.Column('operation', sa.String(length=50), nullable=False),
            sa.Column('input', sa.Text(), nullable=False),
            sa.Column('expected', sa.Text(), nullable=False),
            sa.Column('timeout', sa.Float(), nullable=False, server_default='3.0'),
            sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='medium'),
            sa.Column('memory_limit', sa.Integer(), nullable=True),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['benchmark_id'], ['benchmarks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('tasks', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_tasks_benchmark_id'), ['benchmark_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_tasks_name'), ['name'], unique=False)
    else:
        cols = get_columns('tasks')
        with op.batch_alter_table('tasks', schema=None) as batch_op:
            if 'difficulty' not in cols:
                batch_op.add_column(sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='medium'))
            if 'memory_limit' not in cols:
                batch_op.add_column(sa.Column('memory_limit', sa.Integer(), nullable=True))
            if 'created_at' not in cols:
                batch_op.add_column(sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''))

    # 14. task_runs
    if not table_exists('task_runs'):
        op.create_table('task_runs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('run_id', sa.Integer(), nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('status', sa.String(length=50), nullable=False),
            sa.Column('output', sa.Text(), nullable=False, server_default=''),
            sa.Column('error', sa.Text(), nullable=False, server_default=''),
            sa.Column('duration', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('cpu', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('memory', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('retries', sa.Integer(), nullable=False, server_default='0'),
            sa.ForeignKeyConstraint(['run_id'], ['benchmark_runs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('task_runs', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_task_runs_run_id'), ['run_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_task_runs_status'), ['status'], unique=False)
            batch_op.create_index(batch_op.f('ix_task_runs_task_id'), ['task_id'], unique=False)

    # 15. task_versions
    if not table_exists('task_versions'):
        op.create_table('task_versions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_id', sa.Integer(), nullable=False),
            sa.Column('version', sa.String(length=50), nullable=False, server_default='1.0.0'),
            sa.Column('input', sa.Text(), nullable=False),
            sa.Column('expected', sa.Text(), nullable=False),
            sa.Column('timeout', sa.Float(), nullable=False, server_default='3.0'),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['task_id'], ['tasks.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # 16. artifacts
    if not table_exists('artifacts'):
        op.create_table('artifacts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('run_id', sa.Integer(), nullable=False),
            sa.Column('task_run_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('file_path', sa.String(length=512), nullable=False),
            sa.Column('mime_type', sa.String(length=100), nullable=False, server_default='application/octet-stream'),
            sa.Column('size_bytes', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['run_id'], ['benchmark_runs.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['task_run_id'], ['task_runs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('artifacts', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_artifacts_run_id'), ['run_id'], unique=False)
            batch_op.create_index(batch_op.f('ix_artifacts_task_run_id'), ['task_run_id'], unique=False)

    # 17. evaluation_results
    if not table_exists('evaluation_results'):
        op.create_table('evaluation_results',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('task_run_id', sa.Integer(), nullable=False),
            sa.Column('metric_name', sa.String(length=100), nullable=False),
            sa.Column('score', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('passed', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('details', sa.Text(), nullable=False, server_default=''),
            sa.Column('created_at', sa.String(length=64), nullable=False, server_default=''),
            sa.ForeignKeyConstraint(['task_run_id'], ['task_runs.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        with op.batch_alter_table('evaluation_results', schema=None) as batch_op:
            batch_op.create_index(batch_op.f('ix_evaluation_results_task_run_id'), ['task_run_id'], unique=False)

def downgrade() -> None:
    pass
