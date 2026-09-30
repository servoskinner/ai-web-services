import requests

from schema import FarmRequest

if __name__ == "__main__":

    base = "http://localhost:8000"
    post_to = base + "/predict"

    req = FarmRequest(
        farm_id="FARM-001",
        region="Krasnodar",
        crop_type="wheat",
        area_ha=2500,
        temperature_avg=24.3,
        precipitation_mm=320,
        payment_delay_days=15,
        previous_defaults=0,
        debt=1500000,
    )

    res = requests.post(post_to, json=req.model_dump())
    print(f"Returned code {res.status_code}")
    print(f"Contents:\n{(res.json())}")