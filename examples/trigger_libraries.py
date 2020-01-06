import os
import shutil
import sys
import subprocess
import time

all_libs = [
    'Adafruit_TinyUSB_Arduino',
    'Adafruit_SPIFlash',
]

GH_REPO_TOKEN = os.environ["GH_REPO_TOKEN"]

gh_request = 'curl -X POST -H "Authorization: token {}"'.format(GH_REPO_TOKEN) + \
             ' -H "Accept: application/vnd.github.everest-preview+json"' + \
             ' -H "Content-Type: application/json"' + \
             ' --data \'{"event_type": "rebuild"}\' '

url = 'https://api.github.com/repos/adafruit/{}/dispatches'

for lib in all_libs:
    subprocess.run(gh_request + url.format(lib), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
