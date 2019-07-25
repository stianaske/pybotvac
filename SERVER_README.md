# pybotvac Server

* [Usage](#usage)
  * [Prerequisites](#prerequisites)
  * [Clean](#clean)
  * [Stop cleaning](#stop-cleaning)
* [NO cecurity in this code](#no-security-in-this-code)
* [SystemD for execution](#systemd-for-execution)

## Usage

### Prerequisites
You must create two JSON files in the home directory of the ID the webserver will run as:
 - `robot_identity.json`
 - `robot_cleaning_configuration.json`

An example of `robot_identity.json` would be:
```
{
  "name": "my_robot_name",
  "serial": "OPS01234-0123456789AB",
  "secret": "0123456789ABCDEF0123456789ABCDEF",
  "traits": [
    "maps",
    "persistent_maps"
  ]
}
```

An example of `robot_cleaning_configuration.json` would be:
```
{
  "cleaning_mode": "turbo",
  "navigation_mode": "extra care"
}
```

### Clean
To start the webserver simply run
```
python botvac_server.py
```

To initiate cleaning call the endpoint, from the same server that can be accomplished with:
```
curl -X PUT http://127.0.0.1:8080
```

### Stop cleaning
The HTTP response will describe the cleaning being started:
```
{
  "numeric_cleaning_mode": 2,
  "numeric_category": 4,
  "numeric_navigation_mode": 2,
  "cleaning_mode": "turbo",
  "navigation_mode": "extra care"
}
```

To halt cleaning use the GET verb (like "get my robot back on the dock" - har har):
```
curl -X GET http://127.0.0.1:8080
```

## NO cecurity in this code
Please note that this webserver is not meant to be exposed to an environment with any unknown or bad actors (there is absolutely no security implemented here). Personally, I am running this on a box whose firewall only allows incoming traffic from my home automation controller, which is far more critical and privileged than the box this runs on.

## SystemD for execution
To make this run consistently you can use a SystemD service file like:
```
[Unit]
Description=Neato Robot HTTP Server
After=network-online.target

[Service]
Type=simple
WorkingDirectory=/home/robot_controller
ExecStart=/usr/bin/python pybotvac/botvac_server.py
Restart=always
User=robot_controller

[Install]
WantedBy=multi-user.target
```
