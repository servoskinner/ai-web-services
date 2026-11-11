import requests

from batch import MAX_BATCH_SIZE
from test.common import BASE, FARM, show

if __name__ == "__main__":
    items = [FARM.model_dump()] * (MAX_BATCH_SIZE + 1)
    show(requests.post(BASE + "/batch-predict", json={"items": items}))
