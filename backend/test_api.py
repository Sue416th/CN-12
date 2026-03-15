# -*- coding: utf-8 -*-
import requests
import json
r = requests.post('http://localhost:8000/api/cultural/chat', json={'message': 'hello'})
data = r.json()
with open('result.txt', 'w', encoding='utf-8') as f:
    f.write(data['answer'][:500])
print("Done")
