# xbutil-gui
A Python Tkinter GUI for Xilinx Vitis xbutil program

# Instructions
This program requires Python 3.6 or newer to run. You can run the commands 
below to install Python 3.6 on Ubuntu 16.04:
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install python3.6 python3.6-venv python3.6-tk 
```

## Install Python Tkinter
### Ubuntu
```
sudo apt install python3-tk
```
### Redhat/CentOS 7.x
```
sudo yum install python36-tkinter
```


## Create and activate a Python3 virtual environment
```
python3.6 -m venv venv
. venv/bin/activate
```

## Install required Python packages
`pip install -r requirements.txt`

## Install xbutil
`python setup.py develop`

## Run xbutil-gui
`xbutil_gui`

# Snapshots
## Main window showing all hosts/devices/compute units in a cluster
![image](https://user-images.githubusercontent.com/24323762/108950146-9a024780-761a-11eb-92e7-1ad8df0409d5.png)

## top window
![image](https://user-images.githubusercontent.com/24323762/108950267-c7e78c00-761a-11eb-818e-99faac6baaea.png)

## Power/temperature plot
![image](https://user-images.githubusercontent.com/24323762/108950304-d766d500-761a-11eb-87aa-d407ae2e1f29.png)

## Vccint/Iccint plot

