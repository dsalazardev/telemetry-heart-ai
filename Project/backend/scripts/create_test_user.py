import asyncio
from app.core.database import async_session_maker
from app.models.usuario import Usuario, Medico
from app.core.security import hash_password
from sqlmodel import select

async def create_user():
    async with async_session_maker() as db:
        # Check if user exists
        stmt = select(Usuario).where(Usuario.correo == "juan@test.com")
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            print("Creando usuario juan@test.com...")
            new_user = Usuario(
                documento="12345678",
                nombres="Juan",
                apellidos="Pérez",
                correo="juan@test.com",
                password=hash_password("clave123"),
                telefono="3001234567",
                tipo="medico"
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            
            # Crear perfil de médico
            new_medico = Medico(
                id=new_user.id,
                especialidad="Cardiología",
                licencia="MED-123456",
                telegramChatId="000000"
            )
            db.add(new_medico)
            await db.commit()
            print("¡Usuario y Médico creados exitosamente!")
        else:
            print("El usuario juan@test.com ya existe.")

if __name__ == "__main__":
    asyncio.run(create_user())
