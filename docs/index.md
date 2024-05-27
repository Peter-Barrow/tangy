# Welcome to tangy 🍊

*tangy* is a high performance library to buffer timetags from timetaggers and files and provides soft-realtime analysis.

## About
It stores your timetag data in a circular buffer backed by shared memory allowing you to have multiple client connect to the same buffer.
When streaming data from a device into a tangy buffer this allows you to have multiple connections to the same device facilitating either mulitple lab users or multiple concurrent experiments.
Alternatively, if you have a large file of containing timetags you can read a section into a tangy buffer in one python interpreter and perform analysis on that section in another speeding up exploratory analysis.


## Features
- Support for different timetag formats
- A client-server model for buffering and analysis
- Analysis for:
    - Singles counting
    - Coincidence counting
    - Delay finding

## Installation
```sh
python3 -m pip install tangy
```

### Advanced
Install from git to get the latest version
```sh
python3 -m pip install git+https://gitlab.com/PeterBarrow/tangy.git
```

## Examples

Open a file and read some data
```python
import tangy

target_file = 'tttr_data.ptu'

n = int(1e7)
name = "tagbuffer"
# Open the file
ptu = tangy.PTUFile(target_file, name, n)

# Read some data from the file
for i in range(11):
    start_time = perf_counter()
    a = ptu.read(1e6)
    stop_time = perf_counter()
    run_time += (stop_time - start_time)
    print([ptu.record_count, ptu.count])

# Acquire the buffer
buffer = ptu.buffer()
```

Count coincidences in the last second for channels [0, 1] with a 1ns window
```python
count = buffer.coincidence_count(1, 1e-9, [0, 1])
```

Collect coincidences in the last second for channels [0, 1] with a 1ns window
```python
records = buffer.coincidence_collect(1, 1e-9, [0, 1])
```

Find the delay between channels 0 and 1
```python
result_delay = tangy.find_delay(buffer, 0, 1, 10, resolution=6.25e-9)
delays = [0, result_delay.t0]
```

Count coincidences in the last second for channels [0, 1] with a 1ns window with a delay on channel 1
```python
count = buffer.coincidence_count(1, 1e-9, [0, 1], delays=delays)
```
