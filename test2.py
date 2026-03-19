import urllib.request
content = urllib.request.urlopen("http://localhost:8000/admin.html").read().decode("utf-8")
print("JSON.stringify(spData)" in content)
