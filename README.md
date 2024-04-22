# Welcome to tangy 🍊

*tangy* brings you a method to buffer timetags from devices and files and high performance analysis on that data.

## Installing
```sh
pip install tangy
```

## Example
```python
import tangy as tangy

target_file = 'tttr_data.ptu'

n = int(1e7)
name = "tagbuffer"
ptu = tangy.PTUFile(target_file, name, n)

for i in range(11):
    start_time = perf_counter()
    a = ptu.read(1e6)
    stop_time = perf_counter()
    run_time += (stop_time - start_time)
    print([ptu.record_count, ptu.count])

coincidences = tangy.Coincidences(buffer, [0, 1], [0, 1.6205874491248539e-07])
res = coincidences.collect(0.5e-9, 1)
print(res.count)
print(coincidences.count(0.5e-9, 1))

```
