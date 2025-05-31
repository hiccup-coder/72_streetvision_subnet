from pathlib import Path
from typing import Dict, List
import os

HUGGINGFACE_REPO = os.getenv("HUGGINGFACE_REPO", "natix-network-org")
# HUGGINGFACE_CACHE_DIR: Path = Path.home() / ".cache" / "huggingface"
HUGGINGFACE_CACHE_DIR: Path = "/nvme0n1-disk/hiccup/streetvision-subnet/.cache/huggingface"
IMAGE_DATASETS: Dict[str, List[Dict[str, str]]] = {
    "Roadwork": [
        {"path": f"{HUGGINGFACE_REPO}/roadwork"},
        # {"path": f"natix-network-org/roadwork"},
    ],
}