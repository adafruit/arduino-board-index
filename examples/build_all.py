import os
import shutil
import sys
import subprocess
import time

success_count = 0
fail_count = 0
exit_status = 0

build_format = '| {:55} | {:9} '
build_separator = '-' * 79

SKETCH = 'examples/test/test.ino'

all_boards = [
    # AVR Boards
    'adafruit:avr:flora8',
    'adafruit:avr:bluefruitmicro',
    'adafruit:avr:gemma',
    'adafruit:avr:metro',
    'adafruit:avr:trinket3',
    'adafruit:avr:trinket5',
    'adafruit:avr:protrinket5',
    'adafruit:avr:protrinket5ftdi',
    'adafruit:avr:protrinket3',
    'adafruit:avr:protrinket3ftdi',
    'adafruit:avr:feather328p',
    'adafruit:avr:circuitplay32u4cat',
    'adafruit:avr:itsybitsy32u4_5V',
    'adafruit:avr:itsybitsy32u4_3V',
    'adafruit:avr:adafruit32u4',
    # SAMD Boards
    'adafruit:samd:adafruit_feather_m0',
    'adafruit:samd:adafruit_feather_m0_express',
    'adafruit:samd:adafruit_metro_m0',
    'adafruit:samd:adafruit_circuitplayground_m0',
    'adafruit:samd:adafruit_gemma_m0',
    'adafruit:samd:adafruit_trinket_m0',
    'adafruit:samd:adafruit_itsybitsy_m0',
    'adafruit:samd:adafruit_hallowing',
    'adafruit:samd:adafruit_crickit_m0',
    'adafruit:samd:adafruit_metro_m4:speed=120',
    'adafruit:samd:adafruit_grandcentral_m4:speed=120',
    'adafruit:samd:adafruit_itsybitsy_m4:speed=120',
    'adafruit:samd:adafruit_feather_m4:speed=120',
    'adafruit:samd:adafruit_trellis_m4:speed=120',
    'adafruit:samd:adafruit_pyportal_m4:speed=120',
    'adafruit:samd:adafruit_pyportal_m4_titano:speed=120',
    'adafruit:samd:adafruit_pybadge_m4:speed=120',
    'adafruit:samd:adafruit_metro_m4_airliftlite:speed=120',
    'adafruit:samd:adafruit_pygamer_m4:speed=120',
    'adafruit:samd:adafruit_monster_m4sk:speed=120',
    'adafruit:samd:adafruit_hallowing_m4:speed=120',
    # nRF Boards
    'adafruit:nrf52:feather52832',
    'adafruit:nrf52:feather52840',
    'adafruit:nrf52:cplaynrf52840',
    'adafruit:nrf52:itsybitsy52840',
    'adafruit:nrf52:cluenrf52840'
]

total_time = time.monotonic()

print(build_separator)
print((build_format + '| {:5} |').format('Board', 'Result', 'Time'))
print(build_separator)

for board in all_boards:
    start_time = time.monotonic()
    make_result = subprocess.run("arduino-cli compile --fqbn {} {}".format(board, SKETCH), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    build_duration = time.monotonic() - start_time

    if make_result.returncode == 0:
        success = "\033[32msucceeded\033[0m"
        success_count += 1
    else:
        exit_status = make_result.returncode
        success = "\033[31mfailed\033[0m   "
        fail_count += 1

    print((build_format + '| {:.2f}s |').format(board, success, build_duration))

    if make_result.returncode != 0:
        print(make_result.stdout.decode("utf-8"))

# Build Summary
total_time = time.monotonic() - total_time
print(build_separator)
print("Build Sumamary: {} \033[32msucceeded\033[0m, {} \033[31mfailed\033[0m and took {:.2f}s".format(success_count, fail_count, total_time))
print(build_separator)

sys.exit(exit_status)
