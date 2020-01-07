import os
import shutil
import sys
import subprocess
import time

# sorted alphabetically
all_libs = [
    'Adafruit_9DOF',
    'Adafruit_ADXL343',
    'Adafruit_Arcada',
    'Adafruit_BME280_Library',
    'Adafruit_BMP280_Library',
    'Adafruit_BusIO',
    'Adafruit_EPD',
    'Adafruit-GFX-Library',
    'Adafruit_ICM20649',
    'Adafruit_ILI9341',
    'Adafruit_ImageReader',
    'Adafruit_INA260',
    'Adafruit_LIS2MDL',
    'Adafruit_LIS3MDL',
    'Adafruit_LSM303_Accel',
    'Adafruit_LSM303DLH_Mag',
    'Adafruit_LSM6DS',
    'Adafruit_MAX31865',
    'Adafruit_MCP4728',
    'Adafruit_MLX90640',
    'Adafruit_MSA301',
    'Adafruit_NeoPixel_ZeroDMA',
    'Adafruit_Sensor',
    'Adafruit_SensorLab',
    'Adafruit_SPIFlash',
    'Adafruit-ST7735-Library',
    'Adafruit_TinyUSB_Arduino',
]

GH_REPO_TOKEN = os.environ["GH_REPO_TOKEN"]

gh_request = 'curl -X POST -H "Authorization: token {}"'.format(GH_REPO_TOKEN) + \
             ' -H "Accept: application/vnd.github.everest-preview+json"' + \
             ' -H "Content-Type: application/json"' + \
             ' --data \'{"event_type": "rebuild"}\' '

url = 'https://api.github.com/repos/adafruit/{}/dispatches'

for lib in all_libs:
    subprocess.run(gh_request + url.format(lib), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
