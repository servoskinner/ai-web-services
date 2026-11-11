import requests

from test.common import BASE, FARM, show

if __name__ == "__main__":
    items = [FARM.model_dump() | {"farm_id": f"FARM-00{i}"} for i in range(1, 4)]
    res = requests.post(BASE + "/batch-predict", json={"items": items})
    request_id = res.json()["request_id"]

    print("GET /predictions/{request_id}:")
    show(requests.get(BASE + f"/predictions/{request_id}"))
    print("\nGET /requests/{request_id}/predictions:")
    show(requests.get(BASE + f"/requests/{request_id}/predictions"))
