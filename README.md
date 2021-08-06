# xbutil-gui
A Python Tkinter GUI for Xilinx Vitis xbutil program

# Installation
## OS
xbutil-gui has been tested on CentOS 7.8 and Ubuntu 16.04/18.04.

## Xilinx XRT
[Xilinx XRT](https://github.com/Xilinx/XRT) version 2.8.0 or newer is required 
on every host with Xilinx Alveo Accelerator Cards.

## SSH authentication key
xubtil-gui supports scaning hosts within a cluster. All hosts in the cluster
need to have SSH authentication key set up so you can run commands on remote
hosts with your username and without password. Follow instructions 
on the [SSH Login without password](https://github.com/jimw567/xbutil-gui/wiki/SSH-login-without-password) page to set up SSH authentication key.

## Python
This program requires Python 3.6 or newer to run. 

### Ubuntu 16.04
The default Python on Ubuntu 16.04 is version 3.5. Run the commands below to 
install Python 3.6
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.6 python3.6-venv python3.6-tk 
```

### Redhat/CentOS 7.8
The default Python on CentOS 7.8 is already version 3.6. You only need to 
install Python Tkinter.
```
sudo yum install python36-tkinter python3-tkinter
```

## Create and activate a Python3 virtual environment
```
python3.6 -m venv venv
. venv/bin/activate
```

## Install xbutil GUI as a regular user
`pip install xbutil_gui`

## Install xbutil GUI as a contributor
```
git clone https://github.com/jimw567/xbutil-gui.git
cd xbutil-gui
pip install -r requirements.txt`
python setup.py develop
```

# Run xbutil-gui
`xbutil_gui`

## Configuration File
xbutil_gui only scans the localhost for Alveo cards by default. You can create a configuration $HOME/xbutil-gui-config.json and add additional servers. Below is an example of xbutil-gui-config.json file
```
{
    "clusters": {
        "fpga-cluster1" : ["fpga-node1", "fpga-node2"],
        "localhost": ["localhost"]
    }
}
```
## Snapshots
## Main window showing all hosts/devices/compute units in a cluster
![image](https://user-images.githubusercontent.com/24323762/108950146-9a024780-761a-11eb-92e7-1ad8df0409d5.png)

## top window
![image](https://user-images.githubusercontent.com/24323762/108950267-c7e78c00-761a-11eb-818e-99faac6baaea.png)

## Power/temperature plot
![image](https://user-images.githubusercontent.com/24323762/108950304-d766d500-761a-11eb-87aa-d407ae2e1f29.png)

## Vccint/Iccint plot
![image](https://user-images.githubusercontent.com/24323762/108950325-e2ba0080-761a-11eb-8392-d220b9e90634.png)

# Publish xbutil_gui to PyPI
`./scripts/publish-pypi.sh`

The following modules may need to be upgraded or installed:
```
pip install --upgrade pip
pip install twine
```

