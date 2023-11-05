import requests

while 1:
    url = input("Enter url to submit: ")
    requests.post("http://127.0.0.1:27237/download", headers={"url": url})
    
    # requests.post("http://node2.lunes.host:27237/download", headers={"url": url})