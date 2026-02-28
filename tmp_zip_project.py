import zipfile
import os

files_to_zip = [
    "main.py",
    "seed_buildings.py",
    "index.html",
    "verbrannte_zone.db",
]
dirs_to_zip = ["css", "js", "terrains"]

with zipfile.ZipFile("deploy.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
    for f in files_to_zip:
        if os.path.exists(f):
            zipf.write(f)
    for d in dirs_to_zip:
        if os.path.exists(d):
            for root, dirs, files in os.walk(d):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, file_path)
print("deploy.zip created successfully.")
