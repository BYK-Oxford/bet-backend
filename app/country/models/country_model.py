from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.core.database import Base

class Country(Base):
    __tablename__ = "countries"

    country_id = Column(String, primary_key=True, index=True)
    country_name = Column(String, unique=True, nullable=False)

    leagues = relationship("League", back_populates="country")
    teams = relationship("Team", back_populates="country")
