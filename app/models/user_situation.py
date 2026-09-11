from typing import Optional
from pydantic import BaseModel, Field


class UserSituation(BaseModel):
    age: Optional[int] = Field(default=None)
    residence: Optional[str] = Field(default=None)
    welfare_status: Optional[str] = Field(default=None)
    living_alone: Optional[bool] = Field(default=None)

    care_needs: list[str] = Field(default_factory=list)

    mobility_difficulty: Optional[bool] = Field(default=None)
    meal_difficulty: Optional[bool] = Field(default=None)
    cleaning_difficulty: Optional[bool] = Field(default=None)
    outing_difficulty: Optional[bool] = Field(default=None)

    recent_discharge: Optional[bool] = Field(default=None)

    duplicate_services: list[str] = Field(default_factory=list)
    duplicate_service_unknown: bool = Field(default=True)

    long_term_care_expired: Optional[bool] = Field(default=None)

    urgent: bool = Field(default=False)