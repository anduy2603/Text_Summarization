from __future__ import annotations

import os


def _set_huggingface_offline() -> None:
    overrides = {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    os.environ.update(overrides)
    try:
        import huggingface_hub.constants as hf_constants

        hf_constants.HF_HUB_OFFLINE = True
    except Exception:
        pass
    try:
        import transformers.utils.hub as transformers_hub

        transformers_hub._is_offline_mode = True
    except Exception:
        pass
