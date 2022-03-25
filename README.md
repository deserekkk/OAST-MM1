## Requirements

`python >= 3.6`
`pip`
`numpy`
`scipy`
`pandas`
`matplotlib`

## Setup

### Install system requirements

* _Linux (Debian / Ubuntu):_

```commandline
sudo apt update
sudo apt install python3 python3-pip
```

* _Windows_

https://www.python.org/downloads/

This will install Python as well as `pip`.

### Install Python requirements

1. Make sure Python and `pip` are installed and added to `PATH` system variable.
2. Open terminal or command prompt and in the project directory type:

```commandline
pip3 install -r requirements.txt
```

---

### Usage

First, change the parameters in the [config/config.json](config/config.json)
file.

You can also create your own json file with all needed parameters, for example:

```json
{
  "multithreaded": true,
  "variant": "BEZ",
  "mi_values": [8],
  "lam_values": [0.5, 0.87, 1.23, 1.6, 1.97, 2.33, 2.7, 3.07, 3.43, 3.8, 4.17, 4.53, 4.9, 5.27, 5.63, 6],
  "on_values": [40],
  "off_values": [35],
  "server_counts": [1],
  "simulation_repetitions": 40,
  "time_limit": 3600,
  "events_limit": 50000,
  "seed": 123
}
```

* `multithreaded` - use thread pool for computation. If false all computations
  are carried out in the main thread
* `variant` - what logic of behavior of the system to use: _[A, B, BEZ]_
* `mi_values` - values for mean service rate
* `lam_values` - values for mean arrival rate
* `on_values` - values for mean system on time, only for variants _A_ and _B_
* `off_values` - values for mean system off time, only for variants _A_ and _B_
* `server_counts` - values for server count parameter
* `simulation_repetitions` - count of simulation repetitions
* `time_limit` - time limit for each simulation
* `events_limit` - events limit for each simulation
* `seed` - seed to use for RNG initialization

> **_NOTE_**:
> Parameters that are lists, can contain multiple values, the simulation is run
> on every combination of those parametes.

To run the simulator, use `simulation` script from `simulation` module:

```commandline
python3 -m simulator.simulation
```
