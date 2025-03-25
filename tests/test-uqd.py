from time import sleep
from tangy import UQDLogic16

uqd = UQDLogic16(add_buffer=True, calibrate=False)

for ch in range(uqd.number_of_channels):
    uqd.input_threshold = (ch + 1, 0.1)

buffer = uqd.buffer()

print(buffer)

uqd.start_timetags()

while True:
    # count = uqd.write_to_buffer()
    (count, channels, timestamps) = uqd.read_tags()
    print(f"Got {count} Tags")
    print(channels, timestamps)
    sleep(0.1)
