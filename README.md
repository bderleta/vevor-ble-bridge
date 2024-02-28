# Vevor BLE Bridge

A MQTT-BLE bridge to enable control of Vevor Diesel Heater, using reverse-engineered protocol used by AirHeaterBle application. Tested on Raspberry Pi 5.

![obraz](https://github.com/bderleta/vevor-ble-bridge/assets/4968080/307599a9-bbd1-4864-b016-e079e434a8c6)

## Getting Started

### Dependencies

* Python 3.10+
* [bluepy](https://github.com/IanHarvey/bluepy)
* [paho-mqtt](https://pypi.org/project/paho-mqtt/)

### Installing

* `git clone` this repository and enter the `vevor-ble-bridge` directory
* build docker container: `docker build -t vevor-ble-bridge .`
* prepare your `.env` file (you can start from copying the sample file `.env.sample`)
* run the container interactively to verify it's OK: `docker-compose up`
* if it's working, kill it (Ctrl+C or so) and run detached `docker-compose up -d` and forget about it
* configure your MQTT integration in Home Assistant, if you didn't do it yet, this bridge supports autodiscovery so your device should automatically appear

## Author

* [Bartosz Derleta](https://github.com/bderleta)

## ChatGPT operator / CR / QA

* [Piotr Bigos](https://github.com/piobig2871)

## License

This project is licensed under the GPLv3 license.

## Acknowledgments

* [spin877](https://github.com/spin877/Bruciatore_BLE)
