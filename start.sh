#!/bin/bash

until python /home/pi/HotTub/HotTubController.py > /var/log/hottub.log; do
	echo "HotTubController crashed with exit code $?. Respawning..." > /var/log/hottub.log
	sleep 1
done

