import importlib
from logging import getLogger
from pathlib import Path

import yaml

logger = getLogger(__name__)

_DEFAULT_MANIFEST = Path(__file__).parent / "manifest.yaml"


def load_agents(services_ref, manifest_path: str | Path | None = None) -> dict[str, "BaseAgent"]:
    """Carga agents desde manifest.yaml e inyecta dependencias desde services_ref.
    Cada agent se expone como atributo en services_ref inmediatamente para que
    agents subsiguientes puedan usarlo como dependencia."""
    path = Path(manifest_path) if manifest_path else _DEFAULT_MANIFEST
    if not path.exists():
        logger.warning("Manifest %s no encontrado", path)
        return {}

    with open(path) as f:
        manifest = yaml.safe_load(f)

    agents = {}
    for name, spec in manifest.get("agents", {}).items():
        if not spec.get("enabled", True):
            logger.info("Agent %s deshabilitado, skip", name)
            continue

        mod_path, cls_name = spec["class"].rsplit(".", 1)
        try:
            mod = importlib.import_module(mod_path)
        except ImportError as e:
            logger.error("Error importando %s: %s", mod_path, e)
            continue

        cls = getattr(mod, cls_name, None)
        if cls is None:
            logger.error("Clase %s no encontrada en %s", cls_name, mod_path)
            continue

        deps = {}
        for dep_name in spec.get("deps", []):
            if hasattr(services_ref, dep_name):
                deps[dep_name] = getattr(services_ref, dep_name)
            else:
                logger.warning("Dependencia %s no encontrada en services_ref", dep_name)

        try:
            agent = cls(**deps)
            agents[name] = agent
            attr_name = f"{name}_graph"
            setattr(services_ref, attr_name, agent)
            logger.info("Agent '%s' cargado desde %s", name, spec["class"])
        except Exception as e:
            logger.error("Error instanciando agent '%s': %s", name, e)

    return agents
