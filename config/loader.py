"""Configuration loader for supervisor personalities."""
import yaml
from pathlib import Path
from typing import List
from models.schemas import SupervisorConfig, Stance, Confidence


def load_supervisor_configs(config_path: str = "config/supervisors.yaml") -> List[SupervisorConfig]:
    """Load supervisor configurations from YAML file."""
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Supervisor config not found: {config_path}")

    with open(path, 'r') as f:
        data = yaml.safe_load(f)

    supervisors = []
    for sup_data in data.get('supervisors', []):
        # Convert string stance/confidence to enums
        sup_data['initial_stance'] = Stance(sup_data['initial_stance'])
        sup_data['initial_confidence'] = Confidence(sup_data['initial_confidence'])

        supervisors.append(SupervisorConfig(**sup_data))

    return supervisors


def get_supervisor_by_name(supervisors: List[SupervisorConfig], name: str) -> SupervisorConfig:
    """Get a specific supervisor config by name."""
    for sup in supervisors:
        if sup.name == name:
            return sup
    raise ValueError(f"Supervisor not found: {name}")
