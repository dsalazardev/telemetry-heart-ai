#!/usr/bin/env python3
"""
Script de demo para simular 30 pacientes con datos del dataset Cleveland.
Genera triajes y alertas en la base de datos SQLite local.
"""
import asyncio
import random
from datetime import date, datetime

from app.core.database import engine, async_session_maker
from app.models.usuario import Usuario, Paciente
from app.models.triaje import Triaje, Alerta
from app.core.security import hash_password
from app.utils.estadisticas import run_simulation, generar_resumen
from sqlmodel import SQLModel


async def crear_usuario_y_paciente(db, doc, nombre, correo, fecha_nac):
    usuario = Usuario(
        documento=doc,
        nombres=nombre,
        apellidos="Demo",
        correo=correo,
        password=hash_password("demo123"),
        telefono="3000000000",
        tipo="paciente",
    )
    db.add(usuario)
    await db.commit()
    await db.refresh(usuario)

    paciente = Paciente(id=usuario.id, fechaNacimiento=fecha_nac)
    db.add(paciente)
    await db.commit()
    await db.refresh(paciente)
    return paciente


async def crear_triajes_y_alertas(db, n=30):
    resultados = run_simulation(n_pacientes=n)
    resumen = generar_resumen(resultados)
    print(f"Simulación completada: {resumen}")

    # Crear triajes y alertas en BD
    triajes_creados = 0
    alertas_creadas = 0

    for r in resultados:
        if r["evento"] == "triaje":
            triaje = Triaje(
                probabilidadRiesgo=r["probabilidad"],
                nivelUrgencia=r["nivel"],
                paciente_id=r["paciente_id"],
                fechaEmision=datetime.utcnow(),
            )
            db.add(triaje)
            await db.commit()
            await db.refresh(triaje)
            triajes_creados += 1

            if r["nivel"] == "alto":
                alerta = Alerta(
                    tipo="anomalia",
                    mensaje=f"Riesgo alto detectado para paciente {r['paciente_id']}",
                    paciente_id=r["paciente_id"],
                    triaje_id=triaje.id,
                )
                db.add(alerta)
                await db.commit()
                alertas_creadas += 1

    print(f"Creados: {triajes_creados} triajes, {alertas_creadas} alertas")
    return triajes_creados, alertas_creadas


async def main():
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session_maker() as db:
        # Crear 5 pacientes base
        for i in range(1, 6):
            await crear_usuario_y_paciente(
                db,
                doc=f"DEMO{i:03d}",
                nombre=f"Paciente Demo {i}",
                correo=f"demo{i}@test.com",
                fecha_nac=date(1980 + i, 1, 1),
            )
        print("Pacientes base creados")

        # Generar triajes y alertas
        await crear_triajes_y_alertas(db, n=30)

    print("Demo finalizado correctamente")


if __name__ == "__main__":
    asyncio.run(main())
