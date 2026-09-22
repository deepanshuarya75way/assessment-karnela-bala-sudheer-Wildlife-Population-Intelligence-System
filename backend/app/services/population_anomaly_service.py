from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.population import Population
from app.models.species import Species
from app.models.alert import PopulationAlert

def analyze_population(db:Session):
  species_list = db.scalars(select(Species)).all()
  alerts=[]
  for species in species_list:
    rows=db.scalars(
      select(Population)
      .where(Population.species_id==species.id)
      .order_by(Population.observation_date.desc())
      .limit(2)
    ).all()

    if len(rows)<2 or rows[i].population_count ==0:
      continue
    old=rows[1].population_count
    new=rows[0].population_count
    change=((new-old)/old)*100
    if abs(change)<10:
      continue
    severity=(
      "CRITICAL" if abs(change)>=50 else
      "HIGH" if abs(change)>= 30 else
      "MEDIUM" if abs(change)>=20 else
      "LOW"
    )

    alert=PopulationAlert(
      species_id=species.id,
      severity=severity,
      explanation=f"Population changed by {abs(change):1f}%.",
      status="OPEN",
    )

    db.add(alert)
    alerts.append(alert)

    db.commits()
    return alerts