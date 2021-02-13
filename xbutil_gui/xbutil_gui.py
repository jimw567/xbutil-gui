# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, Toplevel, scrolledtext
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
from pathlib import Path
import json


# global variables
__resource_path__ = Path(__file__).parent / 'resources'
__icon__ = __resource_path__ / 'xbutil-icon.gif'

status_codes = {
    'XRT_NOT_SETUP': {
        'code': 1,
        'message': 'ERROR: xbutil not found. Please set up XRT environment before running this application.'
    }
}
# interval in seconds between xbutil json dumps
XBUTIL_REFRESH_INTERVAL = 5

# show top info
def show_top_info(top_dict):
    global text_top
    if top_dict is None:
        return

    text_top.delete('1.0', tk.END)
    text_top.insert(tk.END, 'Last updated: ' + top_dict['last_updated'] + '\n')
    text_top.insert(tk.END, 'Device: ' + top_dict['device_combo_name'] + '\n\n')

    text_top.insert(tk.END, 'Device Memory Usage:\n')
    MEM_INFO_HEADER_FORMAT = '{0:12s}|{1:12s}|{2:8s}|{3:12s}|{4:20s}'
    MEM_INFO_FORMAT = '{0:12s}|{1:12s}|{2:8d}|{3:<12d}|{4:<20d}'

    text_top.insert(tk.END, 
        MEM_INFO_HEADER_FORMAT.format('Tag', 'Type', 'Temp', 'Size(MB)', 'Usage'))
    text_top.insert(tk.END, '\n')

    for m in top_dict['device_memory']:
        text_top.insert(tk.END, 
            MEM_INFO_FORMAT.format(m['tag'], m['type'], m['temp'], m['size'], m['usage']))
        text_top.insert(tk.END, '\n')
        
    text_top.insert(tk.END, '\nPower: ' + top_dict['power'] + 'W\n')
    
    text_top.insert(tk.END, '\nTotal DMA Transfer Metrics:\n')
    for m in top_dict['dma_metrics']:
        text_top.insert(tk.END, 'Channel ' + str(m['channel_id']) + ': host to card ' + 
                        str(m['host_to_card_bytes']) + 'MB\n')
        text_top.insert(tk.END, 'Channel ' + str(m['channel_id']) + ': card to host ' + 
                        str(m['card_to_host_bytes']) + 'MB\n')

    text_top.insert(tk.END, '\nCompute Unit Usage:\n')
    for c in top_dict['compute_units']:
        text_top.insert(tk.END, 'CU ' + c['base_address'] + ': ' + c['usage'] + '\n')
     
    

def show_top_window():
    global text_top, window_top
    window_top = Toplevel(root_window)
    window_top.title('xbutil GUI - top')
    text_top = scrolledtext.ScrolledText(window_top, width=100, height=80)
    text_top.pack()
    show_top_info(None)
    

# root window
root_window = tk.Tk()
root_window.title('Xilinx xbutil GUI')
root_window_icon = tk.PhotoImage(file=str(__icon__))
root_window.iconphoto(True, root_window_icon)
root_window.grid_columnconfigure(0, weight=0)
root_window.grid_columnconfigure(1, weight=0)
root_window.grid_columnconfigure(2, weight=0)
root_window.grid_columnconfigure(3, weight=1)
root_window.grid_rowconfigure(1, weight=1)

COMBO_WIDTH = 50
cur_grid_row = 0
lable_device = ttk.Label(root_window, text="Device", width=40, anchor='e')
lable_device.grid(row=cur_grid_row, column=1,  sticky='e')
combo_device = ttk.Combobox(root_window, width=COMBO_WIDTH)
#combo_device.bind("<<ComboboxSelected>>", combo_device_selected())
combo_device['values'] = []
combo_device.grid(row=cur_grid_row, column=2, sticky='w')
button_top = ttk.Button(root_window, text="top", command=show_top_window)
button_top.grid(row=cur_grid_row, column=3, sticky='W')
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

# widgets in sub-windows
# xbutil top window
window_top = None
text_top = None

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

    devices_compute_units = get_devices_compute_uints(xbutil_dump_json)
    combo_device_cur_idx = combo_device.current()
    combo_compute_unit['values'] = devices_compute_units['compute_units'][combo_device_cur_idx]
    device_id = devices_compute_units['device_ids'][combo_device_cur_idx]
    device_combo_name = devices_compute_units['device_combo_names'][combo_device_cur_idx]

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

    
    top_dict = {}
    top_dict['device_memory'] = []
    top_dict['dma_metrics'] = []
    top_dict['compute_units'] = []
    top_dict['device_combo_name'] = device_combo_name
    top_dict['last_updated'] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    for d in xbutil_dump_json['devices']:
        if d['device_id'] == device_id:
            top_dict['power'] = d['electrical']['power_consumption_watts']

            # memory topology and usage information
            for m in d['mem_topology']['board']['memory']['memories']:
                #print('memories', m)
                m_dict = {}
                m_dict['tag'] = m['tag']
                m_dict['type'] = m['type']
                m_dict['temp'] = int(m['extended_info'].get('temperature_C', 0))
                m_dict['size'] = int(m['range_bytes'], 0) >> 20
                m_dict['usage'] = int(m['extended_info']['usage']['allocated_bytes'])

                top_dict['device_memory'].append(m_dict)

            # DMA transfer metrics
            for t in d['mem_topology']['board']['direct_memory_accesses']['metrics']:
                t_dict = {}
                t_dict['channel_id'] = t['channel_id']
                t_dict['host_to_card_bytes'] = int(t['host_to_card_bytes'], 0) >> 20
                t_dict['card_to_host_bytes'] = int(t['card_to_host_bytes'], 0) >> 20

                top_dict['dma_metrics'].append(t_dict)

            # compute units
            for c in d['compute_units']:
                c_dict = {}
                c_dict['base_address'] = c['base_address']
                c_dict['usage'] = c['usage']
                top_dict['compute_units'].append(c_dict)


    if window_top is not None and tk.Toplevel.winfo_exists(window_top):
        show_top_info(top_dict)


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
    device_combo_names = []
    device_ids = []
    compute_units = []
    
    if xbutil_dump_json is None:
        return []

    devices_vbnvs = {}
    for d in xbutil_dump_json['system']['host']['devices']:
        devices_vbnvs[d['bdf']] = d['vbnv']

    for d in xbutil_dump_json['devices']:
        device_id = d['device_id']
        device_vbnv = devices_vbnvs[device_id]
        device_ids.append(device_id)
        device_combo_names.append(device_id + ' :: ' + device_vbnv)
        cur_cu = []
        if isinstance(d['compute_units'], list):
            for cu in d['compute_units']:
                cur_cu.append(cu['name'])
        compute_units.append(cur_cu)

    devices_compute_units['device_ids'] = device_ids
    devices_compute_units['device_combo_names'] = device_combo_names
    devices_compute_units['compute_units'] = compute_units

    return devices_compute_units



def main():
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
    scheduler.add_job(update_history, 'interval', [args.json_file], 
                      seconds=XBUTIL_REFRESH_INTERVAL)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=True))

    # refresh every 1 second
    animation_power = animation.FuncAnimation(figure_hist, animate_plot, interval=1000)

    xbutil_dump_json = get_xbutil_dump(args.json_file)
    devices_compute_units = get_devices_compute_uints(xbutil_dump_json)

    combo_device['values'] = devices_compute_units['device_combo_names']
    combo_device.current(0)

    combo_compute_unit['values'] = devices_compute_units['compute_units'][0]
    if len(combo_compute_unit['values']) > 0:
        combo_compute_unit.current(0)

    combo_plot_metric.current(0)
    combo_plot_auto_refresh.current(1)
    root_window.mainloop()


if __name__ == '__main__':
    main()



