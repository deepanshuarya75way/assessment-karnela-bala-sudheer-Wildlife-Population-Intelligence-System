from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.alert import PopulationAlert

def get_alerts(
  db: Session,
  species_id: int | None=None,
  severity: str | None=None,
):
query=select(PopulationAlert).order_by(
  PopulationAlert.created_at.desc()
)
if species_id is not None:
  query = query.where(PopulationAlert.species_id==species_id)

if severity is not None:
  query = query.where(PopulationAlert.severity==severity)
return db.scalars(query).all()

def get_alert(db:Session,alert_id:int):
  return db.get(PopulationAlert,alert_id)

def create_alert(db:Session,species_id:id,severity:str,explanation:str,):
  alert=PopulationAlert(species_id=species_id,severity=severity,explanation=explanation,status="OPEN",)

  db.add(alert)
  db.commit()
  db.refresh(alert)

  return alert

def acknowledge_alert(db:Session,alert: PopulationAlert, note: str | None,):
  alert.status="ACKNOWLEDGED"
  alert.note=note
  alert.acknowledge_at=datetime.utcnow()

  db.commit()
  db.refresh(alert)
  return alert