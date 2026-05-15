from typing import Any, Dict, Optional

import requests


def call_api(url: str, method: str = "GET", headers: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=data)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Unsupported method: {method}"}

        response.raise_for_status()
        return response.json()
    except Exception as exc:
        return {"error": str(exc)}
