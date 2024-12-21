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
                'shortName': node.get('user', {}).get('shortName', 'Unknown')
            }
        })
    print("Node info parsed.")
    return nodes

def on_receive(packet, interface, node_list):
    try:
        if packet['decoded']['portnum'] == 'TEXT_MESSAGE_APP':
            message = packet['decoded']['payload'].decode('utf-8')
            fromnum = packet['fromId']
            shortname = next((node['user']['shortName'] for node in node_list if node['num'] == fromnum), 'Unknown')
            print(f"{shortname} {fromnum}: {message}")
            interface.sendText(message, fromnum)
    except KeyError:
        pass  # Ignore KeyError silently
    except UnicodeDecodeError:
        pass  # Ignore UnicodeDecodeError silently

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
        print("Script terminated by user")
    #    local.disconnect()
        local.close()
	

if __name__ == "__main__":
    main()
