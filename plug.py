import asyncio
from kasa import SmartStrip
import argparse

async def toggle_plug(ip_address, plug_alias):
    # Create a SmartStrip object with the specified IP address
    strip = SmartStrip(ip_address)

    try:
        # Request the latest status
        await strip.update()
        print(f"Searching for plug '{plug_alias}' on Power Strip at {ip_address}...")

        # Find the plug by alias and toggle its state
        for plug in strip.children:
            if plug.alias == plug_alias:
                if plug.is_on:
                    await plug.turn_off()
                    print(f" - Plug '{plug_alias}' turned OFF.")
                else:
                    await plug.turn_on()
                    print(f" - Plug '{plug_alias}' turned ON.")
                return
        else:
            print(f"No plug found with alias '{plug_alias}'.")

    except Exception as e:
        print(f"Error connecting to the power strip at {ip_address}: {e}")

# Set up argument parser
parser = argparse.ArgumentParser(description="Toggle a plug on a Kasa SmartStrip.")
parser.add_argument("ip_address", type=str, help="IP address of the Kasa SmartStrip")
parser.add_argument("plug_alias", type=str, help="Alias of the plug to toggle")

# Parse arguments
args = parser.parse_args()

# Run the async function with the provided arguments
asyncio.run(toggle_plug(args.ip_address, args.plug_alias))
