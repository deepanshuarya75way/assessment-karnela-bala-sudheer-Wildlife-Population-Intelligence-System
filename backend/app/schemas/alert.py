from datetime import datetime

from pydantic import BaseModel,ConfigDict
class AcknowledgeAlertRequest(BaseModel):
  note: str | None = None

  class AlertResponse(BaseModel):
    id:int
    species_id:int
    severity:str
    explanation: str
    status: str
    note: str |None
    created_at: datetime
    acknowledged_at: datetime | None

    model_config=ConfigDict(from_attributes=True)
    