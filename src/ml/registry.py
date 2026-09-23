"""
Reproducible Model Registry for ML Research Framework.
Persists model metadata, feature versions, training parameters, and validation metrics.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from typing import Dict, List, Optional


@dataclass
class ModelRegistryRecord:
    model_name: str
    model_version: str
    target_name: str
    feature_version: str
    dataset_hash: str
    training_period_start: str
    training_period_end: str
    hyperparameters: Dict
    data_sufficiency_status: str
    validation_accuracy: Optional[float]
    oos_accuracy: Optional[float]
    oos_brier_score: Optional[float]
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelRegistry:
    """
    JSON-backed Model Registry for tracking reproducible ML models.
    """

    def __init__(self, registry_filepath: str = "./data/model_registry.json"):
        self.filepath = registry_filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def _load_registry(self) -> List[Dict]:
        if not os.path.exists(self.filepath):
            return []
        try:
            with open(self.filepath, "r") as f:
                return json.load(f)
        except Exception:
            return []

    def _save_registry(self, records: List[Dict]) -> None:
        with open(self.filepath, "w") as f:
            json.dump(records, f, indent=2)

    def register_model(self, record: ModelRegistryRecord) -> None:
        records = self._load_registry()
        # Overwrite if exists with same version & model_name
        records = [r for r in records if not (r.get("model_name") == record.model_name and r.get("model_version") == record.model_version)]
        records.append(asdict(record))
        self._save_registry(records)

    def list_models(self) -> List[Dict]:
        return self._load_registry()

    def get_model(self, model_name: str, model_version: str = "v1.0") -> Optional[Dict]:
        records = self._load_registry()
        for r in records:
            if r.get("model_name") == model_name and r.get("model_version") == model_version:
                return r
        return None
