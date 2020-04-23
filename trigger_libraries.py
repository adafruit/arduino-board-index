import os
import shutil
import sys
import subprocess
import time

# sorted alphabetically
all_libs = [
    'Adafruit-Fingerprint-Sensor-Library',
    'Adafruit-GFX-Library',
    'Adafruit-SSD1351-library',
    'Adafruit-ST7735-Library',
    'Adafruit-Si4713-Library',
    'Adafruit-TPA2016-Library',
    'Adafruit_9DOF',
    'Adafruit_ADS1X15',
    'Adafruit_ADXL343',
    'Adafruit_AM2320',
    'Adafruit_APDS9960',
    'Adafruit_AS726x',
    'Adafruit_Arcada',
    'Adafruit_BME280_Library',
    'Adafruit_BMP280_Library',
    'Adafruit_BusIO',
    'Adafruit_CAP1188_Library',
    'Adafruit_EPD',
    'Adafruit_FONA',
    'Adafruit_FRAM_I2C',
    'Adafruit_HTU21DF_Library',
    'Adafruit_HX8357_Library',
    'Adafruit_ICM20649',
    'Adafruit_ILI9341',
    'Adafruit_INA260',
    'Adafruit_IO_Arduino',
    'Adafruit_ImageReader',
    'Adafruit_LIS2MDL',
    'Adafruit_LIS3DH',
    'Adafruit_LIS3MDL',
    'Adafruit_LPS35HW',
    'Adafruit_LSM303DLH_Mag',
    'Adafruit_LSM303_Accel',
    'Adafruit_LSM6DS',
    'Adafruit_LSM9DS1',
    'Adafruit_MAX31865',
    'Adafruit_MCP4728',
    'Adafruit_MCP9808_Library',
    'Adafruit_MLX90640',
    'Adafruit_MPL115A2',
    'Adafruit_MPL3115A2_Library',
    'Adafruit_MPRLS',
    'Adafruit_MPU6050',
    'Adafruit_MSA301',
    'Adafruit_Motor_Shield_V2_Library',
    'Adafruit_NeoPixel_ZeroDMA',
    'Adafruit_PCT2075',
    'Adafruit_Pixie',
    'Adafruit_RA8875',
    'Adafruit_SHARP_Memory_Display',
    'Adafruit_SHT31'
    'Adafruit_SI1145_Library',
    'Adafruit_SPIFlash',
    'Adafruit_STMPE610',
    'Adafruit_Seesaw',
    'Adafruit_Sensor',
    'Adafruit_SensorLab',
    'Adafruit_Si7021',
    'Adafruit_SoftServo',
    'Adafruit_TCS34725',
    'Adafruit_TLC5947',
    'Adafruit_TLC59711',
    'Adafruit_TinyFlash',
    'Adafruit_TinyUSB_Arduino',
    'Adafruit_VCNL4010',
    'Adafruit_VEML6070',
    'Adafruit_VL53L0X',
    'Adafruit_VL6180X',
    'LPD8806',
    'WaveHC',
]

GH_REPO_TOKEN = os.environ["GH_REPO_TOKEN"]

gh_request = 'curl -X POST -H "Authorization: token {}"'.format(GH_REPO_TOKEN) + \
             ' -H "Accept: application/vnd.github.everest-preview+json"' + \
             ' -H "Content-Type: application/json"' + \
             ' --data \'{"event_type": "rebuild"}\' '

url = 'https://api.github.com/repos/adafruit/{}/dispatches'

for lib in all_libs:
    subprocess.run(gh_request + url.format(lib), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
