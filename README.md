# smipc

[![PyPI](https://img.shields.io/pypi/v/smipc?style=flat-square)](https://pypi.org/project/smipc/)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/smipc?style=flat-square)
[![GitHub](https://img.shields.io/github/license/osom8979/smipc?style=flat-square)](https://github.com/osom8979/smipc/)

Shared Memory IPC

## Motivation

...

## Features

...

## Benchmark Test

CUDA IPC:
```shell
./run --use-cuda server
# after
./run --use-cuda client
```

CPU IPC:
```shell
./run server
# after
./run client
```

## Test Result

Test environment:

* CPU: Intel(R) Xeon(R) Silver 4208 CPU @ 2.10GHz
* GPU: NVIDIA GeForce RTX 3070 Ti
* Data size: 1920 * 1080 * 3 bytes (5.9MBytes)
* Iteration count: 1000

Test Results:

* CPU IPC: 6ms ~ 7ms
* CUDA IPC: 4ms ~ 5ms

## License

See the [LICENSE](./LICENSE) file for details. In summary,
**smipc** is licensed under the **MIT license**.
