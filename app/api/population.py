from fastapi import APIRouter, Path
from pydantic import BaseModel

router = APIRouter()

# Response models
class AgeDurationResponse(BaseModel):
    duration_days: float

@router.get("/province/{province_id}/age-duration", response_model=AgeDurationResponse)
async def get_age_duration(province_id: int = Path(...)):
    """
    Return the calculated age duration for the given province.
    In a full implementation this would call the compiled TypeScript
    `calculateAgeDuration` function. Here we return a placeholder value.
    """
    # Placeholder – in real usage replace with actual calculation
    return {"duration_days": 10.0}


class ApplyDeathsResponse(BaseModel):
    deaths: dict

@router.post("/province/{province_id}/apply-deaths", response_model=ApplyDeathsResponse)
async def apply_deaths(province_id: int = Path(...)):
    """
    Trigger random death calculations for the given province.
    In a full implementation this would call the compiled TypeScript
    `applyRandomDeaths` function. Here we return a placeholder dict.
    """
    # Placeholder – replace with actual call to `applyRandomDeaths`
    return {"deaths": {}}