#!/bin/bash

while true
do 
  ../bin/python3 read_messages_bt.py --ble $MT_BLE
  sudo systemctl restart bluetooth.service
  sleep 60
done
