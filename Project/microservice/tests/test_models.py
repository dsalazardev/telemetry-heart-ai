import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.lectura import Lectura
from app.models.prediccion import Prediccion
from app.models.adapter import Adapter


@pytest.mark.asyncio
async def test_crud_lectura(setup_db, async_session: AsyncSession):
    lectura = Lectura(
        age=60, sex=1, cp=0, trestbps=130, chol=240, fbs=False,
        restecg=1, thalach=140, exang=False, oldpeak=2.0, slope=1, ca=0, thal=2
    )
    async_session.add(lectura)
    await async_session.commit()
    await async_session.refresh(lectura)
    assert lectura.id is not None
    assert lectura.age == 60


@pytest.mark.asyncio
async def test_crud_adapter(setup_db, async_session: AsyncSession):
    adapter = Adapter(
        proveedor="n8n", endpoint="https://example.com", token="test", activo=True
    )
    async_session.add(adapter)
    await async_session.commit()
    await async_session.refresh(adapter)
    assert adapter.id is not None
    assert adapter.proveedor == "n8n"
