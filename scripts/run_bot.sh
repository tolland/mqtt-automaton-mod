#!/bin/bash
# Helper script to run the Minecraft bot with different configurations

set -eu -o pipefail

uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./configs/beets1.yml

uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./configs/beets2.yml

uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./configs/beets3.yml

uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./configs/beets4.yml

uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./configs/wheat.yml

uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./configs/potatoes1.yml

#uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./scripts/canes_big_field.yml

#uv run python ./scripts/baritone_path_client.py --broker mostquitto.lan ./scripts/canes_small_field.yml
