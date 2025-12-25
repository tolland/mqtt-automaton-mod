#!/bin/bash

set -eu -o pipefail

mosquitto_pub -h mosquitto.lan -t baritone/bots -m '#allowBreak false'
mosquitto_pub -h mosquitto.lan -t baritone/bots -m '#allowSprint false'

set -x

pairs=(
    "cane_0001 2"
    "cane_0002 4"
    "cane_0003 5"
    "cane_0004 5"
    "cane_0005 5"
    "cane_0006 4"
    "cane_0007 5"
    "cane_0008 1"
    "cane_0009 5"
    "cane_0010 3"
    "cane_0011 5"
    "cane_0012 5"
    "cane_0013 5"
    "cane_0014 5"
    "cane_0015 5"
    "cane_0016 5"
    "cane_0017 5"
    "cane_0018 5"
    "cane_0019 5"
)

for pair in "${pairs[@]}"; do
    read -r wp delay <<< "$pair"
    mosquitto_pub -h mosquitto.lan   -t baritone/bots -m "#wp goto ${wp}"
    sleep ${delay}
done
