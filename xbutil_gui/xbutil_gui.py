# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, Toplevel, scrolledtext, messagebox
from tksheet import Sheet
import matplotlib.animation as animation
import matplotlib.pyplot as plt
import subprocess
import os
import json
import shutil
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import argparse
import atexit
from pathlib import Path

from xbutil_gui.xbutil_top import XbutilTop
from xbutil_gui.xbutil_plot import XbutilPlot
from xbutil_gui import VERSION, LABEL_WIDTH, COMBO_WIDTH, __icon__, STATUS_CODES, \
                DEFAULT_XBUTIL_REFRESH_INTERVAL


# interval in seconds between xbutil json dumps
auto_refresh_plot_seconds = 0
xbutil_top = XbutilTop()
xbutil_plot = XbutilPlot()


def get_selected_host_device():
    sheet_selected = sheet_cluster.get_currently_selected()
    if len(sheet_selected) == 0:
        messagebox.showinfo("showinfo", "Please select a cell or row on the sheet first.")
        return -1, None, None

    if str(sheet_selected[0]) == 'row':
        selected_row = sheet_selected[1]
    else:
        selected_row = sheet_selected[0]

    selected_host = sheet_cluster.get_cell_data(selected_row, 0)
    selected_device_id_name = sheet_cluster.get_cell_data(selected_row, 1)
    if len(selected_device_id_name) == 0:
        messagebox.showinfo("showinfo", "Please wait until devices are scanned.")
        return -2, None, None

    return 0, selected_host, selected_device_id_name


def show_top_window():
    status, selected_host, selected_device_id_name = get_selected_host_device()
    if status < 0:
        return

    xbutil_top.show_top_window(root_window, selected_host, selected_device_id_name)


def show_plot_window():
    status, selected_host, selected_device_id_name = get_selected_host_device()
    if status < 0:
        return

    xbutil_plot.show_plot_window(root_window, selected_host, selected_device_id_name)

###############################################################################
# root window
###############################################################################
root_window = tk.Tk()
root_window.geometry('1200x400')
root_window.title('Xilinx xbutil GUI ' + VERSION)
root_window_icon = tk.PhotoImage(file=str(__icon__))
root_window.iconphoto(True, root_window_icon)
root_window.grid_columnconfigure(0, weight=0)
root_window.grid_columnconfigure(1, weight=0)
root_window.grid_columnconfigure(2, weight=0)
root_window.grid_columnconfigure(3, weight=1)

cur_grid_row = 0
label_cluster = ttk.Label(root_window, text="Cluster", width=LABEL_WIDTH, anchor='w')
label_cluster.grid(row=cur_grid_row, column=0,  sticky='w')
combo_cluster = ttk.Combobox(root_window, width=COMBO_WIDTH)
combo_cluster['values'] = []
combo_cluster.grid(row=cur_grid_row, column=1, sticky='w')
cur_grid_row = cur_grid_row + 1

# sheet for cluster
sheet_cluster = Sheet(root_window,
                      default_row_index="numbers",
                      total_rows=200,
                      total_columns=4
                      )
sheet_cluster.enable_bindings(("single_select",  # "single_select" or "toggle_select"
                               "drag_select",  # enables shift click selection as well
                               "column_drag_and_drop",
                               "row_drag_and_drop",
                               #"column_select",
                               "row_select",
                               "column_width_resize",
                               "double_click_column_resize",
                               "arrowkeys",
                               #"row_height_resize",
                               #"double_click_row_resize",
                               "right_click_popup_menu",
                               "rc_select",
                               #"rc_insert_column",
                               #"rc_delete_column",
                               #"rc_insert_row",
                               #"rc_delete_row",
                               "copy",
                               "cut",
                               "paste",
                               "delete",
                               "undo",
                               "edit_cell"))
sheet_cluster.grid(row=cur_grid_row, columnspan=4, sticky='nswe')
root_window.grid_rowconfigure(cur_grid_row, weight=1)
sheet_cluster.set_cell_data(0, 0, 'Host')
sheet_cluster.set_cell_data(0, 1, 'Device ID :: Name')
sheet_cluster.set_cell_data(0, 2, 'Compute Unit')
sheet_cluster.set_cell_data(0, 3, 'Last Updated')
sheet_cluster.column_width(column=1, width=400)
sheet_cluster.column_width(column=2, width=400)
sheet_cluster.column_width(column=3, width=200)
cur_grid_row = cur_grid_row + 1

# command buttons for selected host
button_top = ttk.Button(root_window, text="top", command=show_top_window)
button_top.grid(row=cur_grid_row, column=1)
button_plot = ttk.Button(root_window, text="plot", command=show_plot_window)
button_plot.grid(row=cur_grid_row, column=2)
cur_grid_row = cur_grid_row + 1


def get_xbutil_dump(json_file, host='localhost'):
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


# get xbutil dump from each host in round robin fashion every XBUTIL_REFRESH_INTERVAL
def refresh_database(json_file):
    global auto_refresh_host_idx, clusters, auto_refresh_sheet_row, auto_refresh_plot_seconds

    xbutil_dump_json = get_xbutil_dump(json_file)
    if xbutil_dump_json is None:
        return

    devices_compute_units = get_devices_compute_units(xbutil_dump_json)
    selected_cluster = combo_cluster.current()
    refresh_host = clusters[combo_cluster['values'][selected_cluster]][auto_refresh_host_idx]
    auto_refresh_host_idx = auto_refresh_host_idx + 1

    last_udpated = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    for i_dn in range(len(devices_compute_units['device_id_names'])):
        device_id_name = devices_compute_units['device_id_names'][i_dn]
        xbutil_top.generate_top_dict(xbutil_dump_json, refresh_host, device_id_name)
        xbutil_plot.update_history(xbutil_dump_json, refresh_host, device_id_name)
        if len(devices_compute_units['compute_units'][i_dn]) > 0:
            for cu in devices_compute_units['compute_units'][i_dn]:
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, 0, refresh_host)
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, 1, device_id_name)
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, 2, cu)
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, 3, last_udpated)
                auto_refresh_sheet_row = auto_refresh_sheet_row + 1
        else:
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, 0, refresh_host)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, 1, device_id_name)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, 2, 'None')
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, 3, last_udpated)
            auto_refresh_sheet_row = auto_refresh_sheet_row + 1

    sheet_cluster.refresh()
    if auto_refresh_host_idx == len(clusters[combo_cluster['values'][selected_cluster]]):
        auto_refresh_host_idx = 0
        auto_refresh_sheet_row = 1

    xbutil_top.show_top_info()
    xbutil_plot.plot_metrics(auto_refresh_plot_seconds)

    auto_refresh_plot_seconds = auto_refresh_plot_seconds + DEFAULT_XBUTIL_REFRESH_INTERVAL
    root_window.after(DEFAULT_XBUTIL_REFRESH_INTERVAL*1000, refresh_database, json_file)


def get_devices_compute_units(xbutil_dump_json):
    devices_compute_units = {}
    device_id_names = []
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
        device_id_names.append(device_id + '::' + device_vbnv)
        cur_cu = []
        if isinstance(d['compute_units'], list):
            for cu in d['compute_units']:
                cur_cu.append(cu['name'])
        compute_units.append(cur_cu)

    devices_compute_units['device_ids'] = device_ids
    devices_compute_units['device_id_names'] = device_id_names
    devices_compute_units['compute_units'] = compute_units

    return devices_compute_units


def main():
    global plot_metric, prev_cluster_name, clusters, auto_refresh_host_idx, \
           auto_refresh_sheet_row, xbutil_plot

    parser = argparse.ArgumentParser()
    parser.add_argument('--json-file', dest='json_file', default=None,
                        help='Specify a JSON file for getting the data')
    parser.add_argument('--plot-type', dest='plot_metric', default='power',
                        help='Specify plot type: power, temperature, or voltage')
    args = parser.parse_args()
    plot_metric = args.plot_metric
    if args.json_file is None and shutil.which('xbutil') is None:
        print(STATUS_CODES['XRT_NOT_SETUP']['message'])
        exit(STATUS_CODES['XRT_NOT_SETUP']['code'])

    home = os.path.expanduser("~")
    config_file = home + '/.xbutil-gui.json'
    cluster_names = []
    if Path(config_file).exists():
        with open(config_file, 'r') as fp:
            xbutil_config_json = json.load(fp)

        clusters = xbutil_config_json.get('clusters', [])
        for k in clusters.keys():
            cluster_names.append(k)

        combo_cluster['values'] = cluster_names
        if len(cluster_names) > 0:
            combo_cluster.current(0)
            # populate the cluster spreadsheet
            row = 1
            for host in clusters[cluster_names[0]]:
                sheet_cluster.set_cell_data(row, 0, host)
                row = row + 1
            prev_cluster_name = cluster_names[0]
            auto_refresh_host_idx = 0
            auto_refresh_sheet_row = 1

    # add a background task to get xbutil
    #scheduler.add_job(refresh_database, 'interval', [args.json_file],
    #                  seconds=DEFAULT_XBUTIL_REFRESH_INTERVAL)
    #scheduler.start()
    #atexit.register(lambda: scheduler.shutdown(wait=True))

    root_window.after(DEFAULT_XBUTIL_REFRESH_INTERVAL*1000, refresh_database, args.json_file)
    root_window.mainloop()


if __name__ == '__main__':
    main()



