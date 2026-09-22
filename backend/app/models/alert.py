from datetime import datetime

from sqlalchemy import DateTime,ForeignKey,Integer,String,Text
from sqlalchemy.orm import Mapped,mapped_column,relationship

from app.database.base import Base

class PopulationAlert(Base):
  __tablename__="population_alerts"

  id:Mapped[int]=mapped_column(
    Integer,primary_key=True,index=True
  )
  species_id:Mapped[int]=mapped_column(
    ForeignKey("species.id"),
    nullable=False,
    index=True,
  )
  severity: Mapped[str]=mapped_column(String(20),nullable=False)
  explanation: Mapped[str]=mapped_column(Text,nullable=False)

  status: Mapped[str] = mapped_column(
    String(20),
    nullable=False,
    default="OPEN",
  )
  
  note: Mapped[str | None]=mapped_column(
    Text,nullable=True
  )

  created_at: Mapped[datetime | None]= mapped_column(
    DateTime,
    default=default=datetime.utcnow,
    nullable=False,
  )
  
  acknowledged_at: Mapped[datetime | None]= mapped_column(
    DateTime,
    nullable=True,
  )

  species=relationship("Species")