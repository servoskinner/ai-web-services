import requests

from test.common import BASE, FARM, show

if __name__ == "__main__":
    show(requests.post(BASE + "/predict-with-llm", json=FARM.model_dump()))
