"""init

Revision ID: 7468eec37172
Revises: 
Create Date: 2026-06-07 12:24:46.601065

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision: str = '7468eec37172'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Orden correcto para PostgreSQL: tablas sin FK primero, luego con FK

    # FASE 1: Tablas base (sin FKs externas)
    op.create_table('usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('documento', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('nombres', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('apellidos', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('correo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('telefono', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('tipo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_correo'), 'usuarios', ['correo'], unique=True)
    op.create_index(op.f('ix_usuarios_documento'), 'usuarios', ['documento'], unique=True)
    op.create_index(op.f('ix_usuarios_tipo'), 'usuarios', ['tipo'], unique=False)

    op.create_table('patologias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('codigoCie11', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('nombre', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('categoria', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('factorRiesgoCardiaco', sa.Boolean(), nullable=False),
        sa.Column('pesoRiesgoModelo', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('eventos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tipo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('ventanaInicio', sa.DateTime(), nullable=False),
        sa.Column('ventanaFin', sa.DateTime(), nullable=False),
        sa.Column('lecturas', sa.Integer(), nullable=False),
        sa.Column('valorAgregado', sa.JSON(), nullable=True),
        sa.Column('workflow_id', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # FASE 2: Tablas que referencian Usuario
    op.create_table('medicos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('especialidad', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('licencia', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('telegramChatId', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('pacientes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fechaNacimiento', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # FASE 3: Tablas con FKs a pacientes
    op.create_table('perfiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('edad', sa.Integer(), nullable=False),
        sa.Column('sexo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('tipoSangre', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('alergias', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('dispositivos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tipo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('modelo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('sistemaOperativo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('tokenAutenticacion', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('ultimoHeartbeat', sa.DateTime(), nullable=True),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('historiales',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('fechaDiagnostico', sa.Date(), nullable=False),
        sa.Column('nivelSeveridad', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('controlada', sa.Boolean(), nullable=False),
        sa.Column('tratamientoActual', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('observaciones', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('ultimaRevision', sa.DateTime(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('patologia_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ),
        sa.ForeignKeyConstraint(['patologia_id'], ['patologias.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # FASE 4: Tablas con FKs a dispositivos y eventos
    op.create_table('telemetrias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('frecuenciaCardiaca', sa.Float(), nullable=False),
        sa.Column('anomaliaEcg', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('spo2', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('estadoProcesamiento', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('dispositivo_id', sa.Integer(), nullable=False),
        sa.Column('evento_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['dispositivo_id'], ['dispositivos.id'], ),
        sa.ForeignKeyConstraint(['evento_id'], ['eventos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # FASE 5: Triaje (FK a pacientes y medicos)
    op.create_table('triajes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('probabilidadRiesgo', sa.Float(), nullable=False),
        sa.Column('nivelUrgencia', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('factoresCriticos', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('explicacionClinica', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('telegramEnviado', sa.Boolean(), nullable=False),
        sa.Column('atendida', sa.Boolean(), nullable=False),
        sa.Column('diagnosticoConfirmado', sa.Boolean(), nullable=True),
        sa.Column('fechaEmision', sa.DateTime(), nullable=False),
        sa.Column('fechaAtencion', sa.DateTime(), nullable=True),
        sa.Column('workflow_id', sa.Integer(), nullable=True),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('medico_id', sa.Integer(), nullable=True),
        sa.Column('alerta_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['medico_id'], ['medicos.id'], ),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # FASE 6: Alertas (FK a pacientes, medicos, triajes)
    op.create_table('alertas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('tipo', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('mensaje', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('leida', sa.Boolean(), nullable=False),
        sa.Column('atendida', sa.Boolean(), nullable=False),
        sa.Column('fechaEmision', sa.DateTime(), nullable=False),
        sa.Column('fechaAtencion', sa.DateTime(), nullable=True),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('medico_id', sa.Integer(), nullable=True),
        sa.Column('triaje_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['medico_id'], ['medicos.id'], ),
        sa.ForeignKeyConstraint(['paciente_id'], ['pacientes.id'], ),
        sa.ForeignKeyConstraint(['triaje_id'], ['triajes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # FASE 7: Logs (FK a triajes)
    op.create_table('logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('tipoEvento', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('detalle', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column('exitoso', sa.Boolean(), nullable=False),
        sa.Column('errorMsg', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column('triaje_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['triaje_id'], ['triajes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('logs')
    op.drop_table('alertas')
    op.drop_table('triajes')
    op.drop_table('telemetrias')
    op.drop_table('historiales')
    op.drop_table('dispositivos')
    op.drop_table('perfiles')
    op.drop_table('pacientes')
    op.drop_table('medicos')
    op.drop_table('eventos')
    op.drop_table('patologias')
    op.drop_index(op.f('ix_usuarios_tipo'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_documento'), table_name='usuarios')
    op.drop_index(op.f('ix_usuarios_correo'), table_name='usuarios')
    op.drop_table('usuarios')
