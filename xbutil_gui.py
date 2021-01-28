# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.widgets import RadioButtons
import matplotlib.animation as animation
import subprocess
import json
import shutil
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import argparse
import atexit

# global variables
status_codes = {
    'XRT_NOT_SETUP': {
        'code': 1,
        'message': 'ERROR: xbutil not found. Please set up XRT environment before running this application.'
    }
}

# root window
root_window = tk.Tk()
root_window.title('Xilinx xbutil GUI')
root_window_icon = tk.PhotoImage(file='resources/xbutil-icon.png')
root_window.iconphoto(True, root_window_icon)
root_window.grid_columnconfigure(0, weight=1)
root_window.grid_columnconfigure(1, weight=1)
root_window.grid_columnconfigure(2, weight=1)
root_window.grid_columnconfigure(3, weight=1)
root_window.grid_rowconfigure(1, weight=1)

COMBO_WIDTH = 40
cur_grid_row = 0
lable_device = ttk.Label(root_window, text="Device").grid(
    row=cur_grid_row, column=1, sticky='e')
combo_device = ttk.Combobox(root_window, width=COMBO_WIDTH)
combo_device['values'] = []
combo_device.grid(row=cur_grid_row, column=2, sticky='w')
cur_grid_row = cur_grid_row + 1

# compute unit row
lable_compute_unit = ttk.Label(root_window, text="Compute Uint").grid(
    row=cur_grid_row, column=1, sticky='e')
combo_compute_unit = ttk.Combobox(root_window, width=COMBO_WIDTH)
combo_compute_unit['values'] = []
combo_compute_unit.grid(row=cur_grid_row, column=2, sticky='w')
cur_grid_row = cur_grid_row + 1

# Add a dropdown list for plot metric
lable_plot_metric = ttk.Label(root_window, text="Plot metric").grid(
    row=cur_grid_row, column=1, sticky='e')
combo_plot_metric = ttk.Combobox(root_window, width=COMBO_WIDTH)
combo_plot_metric['values'] = ('power', 'temperature', 'voltage')
combo_plot_metric.grid(row=cur_grid_row, column=2, sticky='w')
cur_grid_row = cur_grid_row + 1

## Auto refresh dropdown
lable_plot_auto_refresh = ttk.Label(root_window, text="Auto Refresh interval(s)").grid(
    row=cur_grid_row, column=1, sticky='e')
combo_plot_auto_refresh = ttk.Combobox(root_window, width=COMBO_WIDTH)
combo_plot_auto_refresh['values'] = ('off', '10', '60')
combo_plot_auto_refresh.grid(row=cur_grid_row, column=2, sticky='w')
cur_grid_row = cur_grid_row + 1

# figure, ax = plt.subplots()
figure_dpi = 100
figure_hist = plt.Figure(figsize=(10, 5), dpi=figure_dpi)
plot_hist = figure_hist.add_subplot(111)
canvas_hist = FigureCanvasTkAgg(figure_hist, root_window)
canvas_hist.get_tk_widget().grid(row=cur_grid_row, column=0, columnspan=4, sticky='nsew')
cur_grid_row = cur_grid_row + 1

# Plot navigation toolbar
frame_toolbar = tk.Frame(root_window)
frame_toolbar.grid(row=cur_grid_row, columnspan=4)
toolbar_plot = NavigationToolbar2Tk(canvas_hist, frame_toolbar)


plot_metric = 'power'
time_hist = []
power_hist = []
temp_hist = []
auto_refresh_interval = 10 # seconds between refresh
scheduler = BackgroundScheduler(daemon=True)


def get_xbutil_dump(json_file):
    if json_file is None:
        command = ['/opt/xilinx/xrt/bin/unwrapped/xbutil2', 'examine', 
                   '--format', 'JSON', '--report', 'all']
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        xbutil_dump = p.stdout.read()
        try:
            xbutil_dump_json = json.loads(xbutil_dump.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            print('ERROR: cannot decode json', xbutil_dump)
            xbutil_dump_json = None
    else:
        with open(json_file, 'r') as fp:
            xbutil_dump_json = json.load(fp)

    return xbutil_dump_json


def update_history(json_file):
    xbutil_dump_json = get_xbutil_dump(json_file)

    devices_compute_uints = get_devices_compute_uints(xbutil_dump_json)
    combo_compute_unit['values'] = devices_compute_uints['compute_units'][0]

    if xbutil_dump_json is None:
        return
        
    #time_hist.append(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    fpga_present = False
    for t in xbutil_dump_json['devices'][0]['thermals']:
        if t['location_id'] == 'fpga0' and t['is_present']:
            fpga_present = True
            fpga_temp = float(t['temp_C'])

    if fpga_present:
        time_hist.append(datetime.datetime.now().strftime("%m/%d %H:%M"))
        power_hist.append(float(xbutil_dump_json['devices'][0]['electrical']['power_consumption_watts']))
        temp_hist.append(fpga_temp)


def animate_plot(iter):
    global plot_metric, auto_refresh_interval

    selected_plot_metric = combo_plot_metric.get()
    if selected_plot_metric != plot_metric:
        # always plot when selected metric is changed.
        # set an interval for the initial plot
        auto_refresh_interval = 10
    else:
        if combo_plot_auto_refresh.get() == 'off':
            return
        auto_refresh_interval = int(combo_plot_auto_refresh.get())

        if iter % auto_refresh_interval > 0:
            return

    plot_metric = selected_plot_metric
    if len(power_hist[::auto_refresh_interval]) == 0:
        # nothing to plot yet
        return

    plot_hist.clear()
    if plot_metric == 'power':
        y_hist_dict = {'time': time_hist[::auto_refresh_interval], 'power': power_hist[::auto_refresh_interval]}
        y_hist_df = DataFrame(y_hist_dict, columns=['time', 'power'])
        y_hist_df.plot(kind='line', legend=False, x='time', y='power', ax=plot_hist,
                       color='r', marker='.', fontsize=10)
        plot_hist.set_title('Power(w) History')
    elif plot_metric == 'temperature':
        y_hist_dict = {'time': time_hist[::auto_refresh_interval], 'temp': temp_hist[::auto_refresh_interval]}
        y_hist_df = DataFrame(y_hist_dict, columns=['time', 'temp'])
        y_hist_df.plot(kind='line', legend=False, x='time', y='temp', ax=plot_hist,
                       color='r', marker='.', fontsize=10)
        plot_hist.set_title('Temperature(C) History')


def get_devices_compute_uints(xbutil_dump_json):
    devices_compute_units = {}
    devices = []
    compute_units = []
    
    if xbutil_dump_json is None:
        return []

    for d in xbutil_dump_json['system']['host']['devices']:
        devices.append(d['vbnv'])

    for d in xbutil_dump_json['devices']:
        cur_cu = []
        if isinstance(d['compute_units'], list):
            for cu in d['compute_units']:
                cur_cu.append(cu['name'])
        compute_units.append(cur_cu)

    devices_compute_units['devices'] = devices
    devices_compute_units['compute_units'] = compute_units

    return devices_compute_units


def xbutil_gui_main():
    global plot_metric

    parser = argparse.ArgumentParser()
    parser.add_argument('--json-file', dest='json_file', default=None,
                        help='Specify a JSON file for getting the data')
    parser.add_argument('--plot-type', dest='plot_metric', default='power',
                        help='Specify plot type: power, temperature, or voltage')
    args = parser.parse_args()
    plot_metric = args.plot_metric
    if args.json_file is None and shutil.which('xbutil') is None:
        print(status_codes['XRT_NOT_SETUP']['message'])
        exit(status_codes['XRT_NOT_SETUP']['code'])

    # add a background task to get xbutil dump every second
    scheduler.add_job(update_history, 'interval', [args.json_file], seconds=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=True))

    # refresh every 1 second
    animation_power = animation.FuncAnimation(figure_hist, animate_plot, interval=1000)

    xbutil_dump_json = get_xbutil_dump(args.json_file)
    devices_compute_uints = get_devices_compute_uints(xbutil_dump_json)

    combo_device['values'] = devices_compute_uints['devices']
    combo_device.current(0)

    combo_compute_unit['values'] = devices_compute_uints['compute_units'][0]
    if len(combo_compute_unit['values']) > 0:
        combo_compute_unit.current(0)

    combo_plot_metric.current(0)
    combo_plot_auto_refresh.current(1)
    root_window.mainloop()


if __name__ == '__main__':
    # start the main GUI
    xbutil_gui_main()



