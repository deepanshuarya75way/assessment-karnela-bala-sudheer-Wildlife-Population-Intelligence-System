from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.alerts import get_alerts,get_alert,acknowledge_alert
from app.schemas.alert import AlertResponse,AcknowledgeAlertRequest
from app.services.population_anomaly_service import analyze_population

router=APIRouter(prefix="/alerts",tags=["Alerts"])

@router.get("",
response_model=list[AlertResponse])
def alerts(
  species_id: int | None = None,
  severity: str | None=None,
  db: Session=Depends(get_db),
):
  return get_alerts(db,species_id,severity)

@router.post("/analyze"
response_model=list[AlertResponse])
def analyze(db:Session = Depends(get_db)):
  return analyze_population(db)

@router.patch("/{alert_id}/acknowledge",response_model=AlertResponse)
def acknowledge(
  alert_id: int,
  data: AcknowledgeAlertRequest,
  db: Session = Depends(get_db),
):
  alert=get_alert(db,alert_id)

  if not alert:
    raise HTTPException(404,"Alert not found")

  return acknowledge_alert(db,alert,data.note)