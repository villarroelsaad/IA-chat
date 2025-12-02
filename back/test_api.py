import requests

def test_chat():
    url = 'http://127.0.0.1:8000/chat'
    payload = {'message': 'Tengo 2 perros'}
    r = requests.post(url, json=payload)
    print('Status:', r.status_code)
    print('Response:', r.json())

if __name__ == '__main__':
    test_chat()
