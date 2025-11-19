from pydantic import BaseModel, ConfigDict

from SEVEN.energy import DEFAULT_CLOUD_PROFILE, DEFAULT_LOCAL_PROFILE
from elia_chat.config import EliaChatModel


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    selected_model: EliaChatModel
    system_prompt: str
    local_profile: str = DEFAULT_LOCAL_PROFILE.value
    cloud_profile: str = DEFAULT_CLOUD_PROFILE.value
