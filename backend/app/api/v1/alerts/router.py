from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.repositories.alerts import get_alerts,get_alert,acknowledge_alert
from app.schemas.alert import AlertResponse,AcknowledgeAlertRequest
from app.services.population_anomaly_service import analyze_population

router=APIRouter(prefix="/alerts",tags=["Alerts"])

@router.get("",

)