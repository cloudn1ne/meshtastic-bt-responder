import time
import sys
import argparse
from pubsub import pub
#from meshtastic.serial_interface import BLEInterface
from meshtastic.ble_interface import BLEInterface
from meshtastic import portnums_pb2


def get_node_info(ble):
    print("Initializing BLEInterface to get node info...")
    local = BLEInterface(ble)

    node_info = local.nodes
    local.close()
    print("Node info retrieved.")
    return node_info

def parse_node_info(node_info):
    print("Parsing node info...")
    nodes = []
    for node_id, node in node_info.items():
        nodes.append({
            'num': node_id,
            'user': {
                'shortName': node.get('user', {}).get('shortName', 'Unknown'),
		'longName': node.get('user', {}).get('longName', 'Unknown')
            }
        })
    print("Node info parsed.")
    return nodes

def on_receive(packet, interface, node_list):
    try:
        print()
        print("-----------------------------------------------------------")
        debugPacket(packet, interface, node_list)
        if packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            fromnum = packet['fromId']
            message = packet['decoded']['payload'].decode('utf-8')
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            longname = next((node['user']['longName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            print(f"<< RX: {shortname} ({longname}) {fromnum}: {message}")

            # send back what we got if we did receive it directly and not via a broadcast  
            if idToHex(packet['to']) != "!ffffffff":
                print(f">> TX: sending AUTO REPLY to {shortname} {fromnum}")
                interface.sendText("reply to "+shortname+" with original message: "+message, destinationId=fromnum)
    except KeyError:
        pass  # Ignore KeyError silently
    except UnicodeDecodeError:
        pass  # Ignore UnicodeDecodeError silently

def debugPacket(packet, interface, node_list):
    print("Received packet:")
    print(f"  From: {packet['from']} / {idToHex(packet['from'])}")
    if 'fromId' in packet:
        fromnum = packet['fromId']
        shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
        longname = next((node['user']['longName'] for node in node_list if node['num'] == fromnum), 'Unknown')
        print(f"  From: {shortname} ({longname})")
    print(f"  To: {packet['to']} / {idToHex(packet['to'])}")
    if 'channel' in packet:
        print(f"  Channel: {packet['channel']}")
    if 'rxSnr' in packet:
        print(f"  SNR: {packet['rxSnr']}")
    if 'rxRssi' in packet:
        print(f"  RSSI: {packet['rxRssi']}")
    if 'hopLimit' in packet:
        print(f"  Hop Limit: {packet['hopLimit']}")
    if 'hopStart' in packet:
        print(f"  Hop Start: {packet['hopStart']}")
    if 'priority' in packet:
        print(f"  Priority: {packet['priority']}")
    if 'viaMqtt' in packet:
        print(f"  via MQTT: {packet['viaMqtt']}")

    if 'decoded' in packet:
        print(f"  Port Number: {packet['decoded'].get('portnum', 'N/A')}")
        
        if packet['decoded'].get('portnum') == 'NODEINFO_APP':
            print("  Node Information:")
            node_info = packet['decoded'].get('user', {})
            print(f"    ID: {node_info.get('id', 'N/A')}")
            print(f"    Long Name: {node_info.get('longName', 'N/A')}")
            print(f"    Short Name: {node_info.get('shortName', 'N/A')}")
            print(f"    MAC Address: {node_info.get('macaddr', 'N/A')}")
            print(f"    Hardware Model: {node_info.get('hwModel', 'N/A')}")
            if 'role' in packet:
                print(f"    Role: {node_info.get('role', 'N/A')}")
            if 'isLicensed' in packet:
                print(f"    Role: {node_info.get('isLicensed', 'N/A')}")
            if 'hopsAway' in packet:
                print(f"    Hops Away: {packet['hopsAway']}")

        elif packet['decoded'].get('portnum') == 'POSITION_APP':
            if 1 == 0:
              print("  Position:")
              position = packet['decoded']['position']
              print(f"    Latitude: {position.get('latitude', 'N/A')}")
              print(f"    Longitude: {position.get('longitude', 'N/A')}")
              print(f"    Altitude: {position.get('altitude', 'N/A')}")
              if 'PDOP' in position:
                  print(f"    PDOP: {position.get('PDOP', 'N/A')}")
              if 'ground_track' in position:
                  print(f"    Ground Track: {position.get('ground_track', 'N/A')}")
              if 'sats_in_view:' in position:
                  print(f"    Satellites in View: {position.get('sats_in_view:', 'N/A')}")


        elif packet['decoded'].get('portnum') == 'TEXT_MESSAGE_APP':
            print("  Text Message:")
            print(f"    Text: {packet['decoded']['text']}")

        elif packet['decoded'].get('portnum') == 'TELEMETRY_APP':
            if 1 == 0:
              print("  Telemetry:")
              telemetry = packet['decoded'].get('telemetry', {})
              print(f"    Time: {telemetry.get('time', 'N/A')}")
              print("    Device Metrics:")

              device_metrics = telemetry.get('deviceMetrics', {})
              if device_metrics:
                  print(f"      Battery Level: {device_metrics.get('batteryLevel', 'N/A')}")
                  print(f"      Voltage: {device_metrics.get('voltage', 'N/A')}")
                  print(f"      Channel Utilization: {device_metrics.get('channelUtilization', 'N/A')}")
                  print(f"      Air Utilization Tx: {device_metrics.get('airUtilTx', 'N/A')}")
                  print(f"      Uptime Seconds: {device_metrics.get('uptimeSeconds', 'N/A')}")

              power_metrics = telemetry.get('powerMetrics', {})
              if power_metrics:
                  print("    Power Metrics:")
                  print(f"      CH1 Voltage: {power_metrics.get('ch1_voltage', 'N/A')}")
                  print(f"      CH1 Current: {power_metrics.get('ch1_current', 'N/A')}")
                  print(f"      CH2 Voltage: {power_metrics.get('ch2_voltage', 'N/A')}")
                  print(f"      CH2 Current: {power_metrics.get('ch2_current', 'N/A')}")

              environment_metrics = telemetry.get('environmentMetrics', {})
              if environment_metrics:
                  print("    Environment Metrics:")
                  print(f"      Temperature: {environment_metrics.get('temperature', 'N/A')}")
                  print(f"      Relative Humidity: {environment_metrics.get('relativeHumidity', 'N/A')}")
                  print(f"      Barometric Pressure: {environment_metrics.get('barometricPressure', 'N/A')}")

        elif packet['decoded'].get('portnum') == 'NEIGHBORINFO_APP':
            # Neighbor Information
            print("  Neighbor Information:")
            message = mesh_pb2.NeighborInfo()
            payload_bytes = packet['decoded'].get('payload', b'')
            message.ParseFromString(payload_bytes)
            print(f"    Node ID: {message.node_id} / {idToHex(message.node_id)}")
            print(f"    Last Sent By ID: {message.last_sent_by_id}")
            print(f"    Node Broadcast Interval (secs): {message.node_broadcast_interval_secs}")
            print("    Neighbors:")
            for neighbor in message.neighbors:
                print(f"      Neighbor ID: {neighbor.node_id} / {idToHex(neighbor.node_id)}")
                print(f"        SNR: {neighbor.snr}")

        elif packet['decoded'].get('portnum') == 'RANGE_TEST_APP':
            print("  Range Test Information:")
            payload = packet['decoded'].get('payload', b'')
            print(f"    Payload: {payload.decode()}")
        
        elif packet['decoded'].get('portnum') == 'STORE_FORWARD_APP':
            print("  Store Forward Information:")
            message = storeforward_pb2.StoreAndForward()
            payload_bytes = packet['decoded'].get('payload', b'')
            message.ParseFromString(payload_bytes)
            if message.HasField('stats'):
                print(f"    Statistics: {message.stats}")
            if message.HasField('history'):
                print(f"    History: {message.history}")
            if message.HasField('heartbeat'):
                print(f"    Heartbeat: {message.heartbeat}")

        elif packet['decoded'].get('portnum') == 'ADMIN_APP':
            print("  Administrative Information:")
            payload = packet['decoded'].get('payload', b'')
            print(f"    Payload: {payload}")
            admin_info = packet['decoded'].get('admin', {})
            if 'getChannelResponse' in admin_info:
                response = admin_info['getChannelResponse']
                print("    Get Channel Response:")
                print(f"      Index: {response.get('index', 'N/A')}")
                print("      Settings:")
                settings = response.get('settings', {})
                for key, value in settings.items():
                    print(f"        {key}: {value}")

        elif packet['decoded'].get('portnum') == 'PAXCOUNTER_APP':
            print("  Paxcounter Information:")
            message = paxcount_pb2.Paxcount()
            payload_bytes = packet['decoded'].get('payload', b'')
            message.ParseFromString(payload_bytes)
            print(f"    Wifi: {message.wifi}")
            print(f"    BLE: {message.ble}")
            print(f"    Uptime: {message.uptime}")
        
        else:
            print(f"  Decoded packet does not contain data we are looking for: {packet['decoded'].get('portnum', 'N/A')}")
    else:
        print("  No 'decoded' key found in the packet. Our node doesn't have the encryption key!")
        
    print()

def idToHex(nodeId):
    return '!' + hex(nodeId)[2:]


def main():
    parser = argparse.ArgumentParser("read_messages_bt")
    parser.add_argument("--ble", help="Shortname of the Meshtastic Device (needs to have been paired once already).", type=str)
    args = parser.parse_args()

    print(f"Using Bluetooth: {args.ble}")

    # Retrieve and parse node information
    node_info = get_node_info(args.ble)
    node_list = parse_node_info(node_info)

    # Print node list for debugging
    print("Node List:")
    for node in node_list:
        print(node)

    # Subscribe the callback function to message reception
    def on_receive_wrapper(packet, interface):
        on_receive(packet, interface, node_list)

    pub.subscribe(on_receive_wrapper, "meshtastic.receive")
    print("Subscribed to meshtastic.receive")

    # Set up the BLEInterface for message listening
    local = BLEInterface(args.ble)
    print("BLEInterface setup for listening.")

    # Keep the script running to listen for messages
    try:
        while True:
            sys.stdout.flush()
            time.sleep(1)  # Sleep to reduce CPU usage
    except KeyboardInterrupt:
        print("Script terminated by user - please stand by while i disconnect from the Meshtastic node ...")
        local.close()
    except BLEInterface.BLEError as ble_err:
        print(f"Caught Meshtastic BLEInterface.BLEError: {ble_err}")
    
    except BleakError as bleak_err:
        print(f"Caught BleakError: {bleak_err}")
    
    except Exception as e:
        print(f"Caught a general exception: {e}")	

if __name__ == "__main__":
    main()
