import requests

from test.common import BASE, show

if __name__ == "__main__":
    req = {
        "prompt": "Объясни, что такое агроскоринг",
        "model": "no-such-model",
    }
    show(requests.post(BASE + "/llm/chat", json=req))
