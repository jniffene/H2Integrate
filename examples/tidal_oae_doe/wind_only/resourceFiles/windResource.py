import requests

API_KEY = "Efc0xyGTwh64msKRQh7XGwsNXhyCE5eJyC7hYJXt"
NLR_API_EMAIL="james.niffenegger@nlr.gov"
latitude  =   60.70251  #Kustatan
longitude = -151.70409 #Kustatan

url = f"https://developer.nlr.gov/api/wind-toolkit/v2/wind/wtk-led-alaska-download.json?api_key={API_KEY}"

payload = f"api_key={API_KEY}&attributes=winddirection_80m&names=2018&utc=true&leap_day=false&interval=60&email={NLR_API_EMAIL}&wkt=POINT({latitude} {longitude})"

headers = {
    'content-type': "application/x-www-form-urlencoded",
    'cache-control': "no-cache"
}

response = requests.request("POST", url, data=payload, headers=headers)

print(response.text)