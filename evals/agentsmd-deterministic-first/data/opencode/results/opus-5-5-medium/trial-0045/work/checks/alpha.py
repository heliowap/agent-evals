import json, time
start = time.monotonic_ns()
time.sleep(0.2)
end = time.monotonic_ns()
open('alpha-timing.json', 'w').write(json.dumps([start, end]))
print(17)
