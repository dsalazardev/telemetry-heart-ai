"""add microservice tables

Revision ID: 7468eec37173
Revises: 7468eec37172
Create Date: 2026-06-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = '7468eec37173'
down_revision = '7468eec37172'
branch_labels = ("microservice",)
depends_on = "7468eec37172"


def upgrade() -> None:
    # Create lecturas table
    op.create_table(
        'lecturas',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('age', sa.Integer(), nullable=False),
        sa.Column('sex', sa.Integer(), nullable=False),
        sa.Column('cp', sa.Integer(), nullable=False),
        sa.Column('trestbps', sa.Integer(), nullable=False),
        sa.Column('chol', sa.Integer(), nullable=False),
        sa.Column('fbs', sa.Boolean(), nullable=False),
        sa.Column('restecg', sa.Integer(), nullable=False),
        sa.Column('thalach', sa.Integer(), nullable=False),
        sa.Column('exang', sa.Boolean(), nullable=False),
        sa.Column('oldpeak', sa.Float(), nullable=False),
        sa.Column('slope', sa.Integer(), nullable=False),
        sa.Column('ca', sa.Integer(), nullable=False),
        sa.Column('thal', sa.Integer(), nullable=False),
        sa.Column('target', sa.Boolean(), nullable=True),
        sa.Column('fechaCreacion', sa.DateTime(), nullable=False),
    )
    
    # Create predicciones table
    op.create_table(
        'predicciones',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('versionModelo', sa.String(), nullable=False),
        sa.Column('probabilidad', sa.Float(), nullable=False),
        sa.Column('clasificacion', sa.String(), nullable=False),
        sa.Column('importanciaVariables', sa.JSON(), nullable=True),
        sa.Column('tiempoMs', sa.Float(), nullable=False),
        sa.Column('fecha', sa.DateTime(), nullable=False),
        sa.Column('metadataTecnica', sa.JSON(), nullable=True),
    )
    
    # Create evaluaciones table
    op.create_table(
        'evaluaciones',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('fechaEvaluacion', sa.DateTime(), nullable=False),
        sa.Column('origenDatos', sa.String(), nullable=False),
        sa.Column('paciente_id', sa.Integer(), nullable=False),
        sa.Column('lectura_id', sa.Integer(), nullable=False),
        sa.Column('prediccion_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['lectura_id'], ['lecturas.id']),
        sa.ForeignKeyConstraint(['prediccion_id'], ['predicciones.id']),
    )
    
    # Create documentos table
    op.create_table(
        'documentos',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('titulo', sa.String(), nullable=False),
        sa.Column('contenido', sa.Text(), nullable=False),
        sa.Column('embedding', sa.ARRAY(sa.Float()), nullable=True),
        sa.Column('fuente', sa.String(), nullable=False),
        sa.Column('fechaIndexacion', sa.DateTime(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('prediccion_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['prediccion_id'], ['predicciones.id']),
    )
    
    # Create adapters table
    op.create_table(
        'adapters',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('proveedor', sa.String(), nullable=False),
        sa.Column('endpoint', sa.String(), nullable=False),
        sa.Column('flujo', sa.JSON(), nullable=True),
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('activo', sa.Boolean(), nullable=False),
        sa.Column('fechaCreacion', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('adapters')
    op.drop_table('documentos')
    op.drop_table('evaluaciones')
    op.drop_table('predicciones')
    op.drop_table('lecturas')
