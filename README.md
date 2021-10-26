# ZettaSpotBlockChecker

A simple tools for RCS Zetta to look for split stations based on a name pattern and to compare spotBlock duration on each station.

## Get Started

- Clone this project
- Copy config-sample.json to config.json and fill it with your information
- Launch splitStationFinder.py. It will create a splitStationFinder.json file including all station find using the pattern
- Launch zettaSpotBlockChecker.py to check and compare duration of the spot block.

## Usage
```bash
usage: zettaSpotBlockChecker.py [-h] [-v] [-d DELTA]

optional arguments:
-h, --help            show this help message and exit
-v, --verbose         Set log level to debug
-d DELTA, --delta 
                      DELTA Set the delta of day(s) from today to check. If not, delta is 0
```
