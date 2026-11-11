import requests

from schema import FarmRequest

BASE = "http://localhost:8000"

FARM = FarmRequest(
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


def show(res: requests.Response) -> None:
    print(f"Returned code {res.status_code}")
    print(f"X-Request-ID: {res.headers.get('X-Request-ID')}")
    print(f"X-Process-Time: {res.headers.get('X-Process-Time')}")
    print(f"Contents:\n{res.json()}")
