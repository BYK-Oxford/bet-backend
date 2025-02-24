from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class TeamAlias(Base):
    __tablename__ = "team_aliases"

    alias_id = Column(String, primary_key=True, index=True)
    alias_name = Column(String, unique=True, nullable=False)
    team_id = Column(String, ForeignKey("teams.team_id"), nullable=False)

    team = relationship("Team", back_populates="aliases")
