import requests

from test.common import BASE, show

if __name__ == "__main__":
    req = {
        "prompt": "Что такое агроскоринг",
        "model": "auto",
        "temperature": 0.3,
        "max_tokens": 300,
    }
    show(requests.post(BASE + "/llm/chat", json=req))
