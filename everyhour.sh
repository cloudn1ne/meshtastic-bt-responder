#!/bin/bash

while true
do
 while timeout -k 1800 1800 ../bin/python3 read_messages_bt.py --ble $MT_BLE; do
   sudo systemctl restart bluetooth.service
   sleep 2
 done
 sudo systemctl restart bluetooth.service
done
