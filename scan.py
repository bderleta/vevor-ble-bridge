from bluepy.btle import Scanner, DefaultDelegate


class ScanDelegate(DefaultDelegate):
    def __init__(self):
        DefaultDelegate.__init__(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            print("Discovered device", dev.addr)
        elif isNewData:
            print("Received new data from", dev.addr)


print("Creating scanner...")
scanner = Scanner().withDelegate(ScanDelegate())
print("Scanning...")
devices = scanner.scan(10.0)
print("Finished.")

for dev in devices:
    print(f"Device {dev.addr} ({dev.addrType}), RSSI={dev.rssi} dB")
    for adtype, desc, value in dev.getScanData():
        print(f"{desc} = {value}")
