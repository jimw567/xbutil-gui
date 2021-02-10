# xbutil-gui
A Python Tkinter GUI for Xilinx Vitis xbutil program

# Instructions
This program requires Python 3.5 or newer to run.

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
python3 -m venv venv
. venv/bin/activate
```

## Install required Python packages
`pip install -r requirements.txt`

## Install xbutil
`python setup.py develop`

## Run xbutil-gui
`xbutil_gui`
