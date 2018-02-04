#!/bin/bash

until python /home/pi/HotTub/HotTubController.py; do
	echo "HotTubController crashed with exit code $?. Respawning..." >&2
	sleep 1
done

