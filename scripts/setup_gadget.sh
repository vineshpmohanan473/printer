#!/bin/bash
# Setup USB Printer Gadget on Raspberry Pi 4

echo "Cleaning old gadget..."
sudo modprobe -r g_printer 2>/dev/null
sudo rm -rf /sys/kernel/config/usb_gadget/printer_gadget 2>/dev/null

echo "Loading libcomposite..."
sudo modprobe libcomposite

cd /sys/kernel/config/usb_gadget
sudo mkdir printer_gadget
cd printer_gadget

# Device descriptors
sudo sh -c 'echo 0x1d6b > idVendor'
sudo sh -c 'echo 0x0104 > idProduct'
sudo sh -c 'echo 0x0100 > bcdDevice'
sudo sh -c 'echo 0x0200 > bcdUSB'

# Strings
sudo mkdir -p strings/0x409
sudo sh -c 'echo "0123456789" > strings/0x409/serialnumber'
sudo sh -c 'echo "Raspberry Pi" > strings/0x409/manufacturer'
sudo sh -c 'echo "USB Printer Gadget" > strings/0x409/product'

# Configuration
sudo mkdir -p configs/c.1
sudo sh -c 'echo 120 > configs/c.1/MaxPower'
sudo sh -c 'echo 0x80 > configs/c.1/bmAttributes'
sudo mkdir -p configs/c.1/strings/0x409
sudo sh -c 'echo "Printer Config" > configs/c.1/strings/0x409/configuration'

# Function
sudo mkdir -p functions/printer.usb0
sudo ln -s functions/printer.usb0 configs/c.1/

# Bind to UDC
sudo sh -c 'echo fe980000.usb > UDC'

echo "USB Printer Gadget setup done."
