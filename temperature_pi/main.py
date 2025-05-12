import requests
import time

params = {
    'temperature': 26.6,
    'humidity': 49
    }
while True:   
    respone = requests.post('http://10.198.98.181:5000//add', data=params)
    time.sleep(2)