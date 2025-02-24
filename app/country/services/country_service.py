from sqlalchemy.orm import Session
from app.country.models.country_model import Country
import uuid

class CountryService:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_country(self, division: str):
        """Determine country from division and get or create the country record."""
        # Map division codes to countries (in reverse)
        division_country_map = {
            "E0": "England",
            "E1": "England",
            "SC0": "Scotland",
            "SC1": "Scotland"
        }

        # Get country name from division
        country_name = division_country_map.get(division)

        if not country_name:
            raise ValueError(f"Unknown division code: {division}")

        # Check if country already exists in the database
        country = self.db.query(Country).filter(Country.country_name == country_name).first()

        if not country:
            # If the country doesn't exist, create and save it
            country = Country(
                country_id=str(uuid.uuid4()),  # Generate unique country ID
                country_name=country_name      # Save the corresponding country name
            )
            self.db.add(country)
            self.db.commit()
            self.db.refresh(country)

        return country
