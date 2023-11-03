import requests

while 1:
    url = input("Enter url to submit: ")
    requests.post("http://127.0.0.1:5000/download", headers={"url": url})