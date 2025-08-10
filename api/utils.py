
# utils.py
import requests

def make_request(url: str, headers: dict = None, params: dict = None):
	try:
		response = requests.get(url, headers=headers, params=params)
		response.raise_for_status()
		return response.json()
	except requests.RequestException as e:
		return {"error": str(e)}
