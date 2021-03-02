# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, Toplevel, scrolledtext, messagebox
from tksheet import Sheet
import subprocess
import os
import json
import shutil
import datetime
import argparse
from pathlib import Path

from xbutil_gui.xbutil_top import XbutilTop
from xbutil_gui.xbutil_plot import XbutilPlot
from xbutil_gui.xbutil_handler import get_devices_compute_units, \
                                      get_xbutil_dump
from xbutil_gui import VERSION, LABEL_WIDTH, COMBO_WIDTH, STATUS_CODES, \
                DEFAULT_XBUTIL_REFRESH_INTERVAL, __resource_path__, __icon__, \
                SHEET_TOTAL_ROWS, SHEET_TOTAL_COLS,  \
                SHEET_HOST_COL, SHEET_DEVICE_COL, SHEET_CU_COL, SHEET_CU_STATUS_COL, \
                SHEET_CU_USAGE_COL, SHEET_LAST_UPDATED_COL


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
root_window.geometry('1500x400+20+20')
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
                      total_rows=SHEET_TOTAL_ROWS,
                      total_columns=SHEET_TOTAL_COLS
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
sheet_cluster.set_cell_data(0, SHEET_HOST_COL, 'Host')
sheet_cluster.set_cell_data(0, SHEET_DEVICE_COL, 'Device ID::Shell')
sheet_cluster.set_cell_data(0, SHEET_CU_COL, 'Compute Unit (CU)')
sheet_cluster.set_cell_data(0, SHEET_CU_STATUS_COL, 'CU Status')
sheet_cluster.set_cell_data(0, SHEET_CU_USAGE_COL, 'CU Usage')
sheet_cluster.set_cell_data(0, SHEET_LAST_UPDATED_COL, 'Last Updated')
sheet_cluster.column_width(column=SHEET_HOST_COL, width=150)
sheet_cluster.column_width(column=SHEET_DEVICE_COL, width=500)
sheet_cluster.column_width(column=SHEET_CU_COL, width=400)
sheet_cluster.column_width(column=SHEET_CU_STATUS_COL, width=100)
sheet_cluster.column_width(column=SHEET_CU_USAGE_COL, width=100)
sheet_cluster.column_width(column=SHEET_LAST_UPDATED_COL, width=200)
cur_grid_row = cur_grid_row + 1

# command buttons for selected host
button_top = ttk.Button(root_window, text="top", command=show_top_window)
button_top.grid(row=cur_grid_row, column=1)
button_plot = ttk.Button(root_window, text="plot", command=show_plot_window)
button_plot.grid(row=cur_grid_row, column=2)
cur_grid_row = cur_grid_row + 1


def update_sheet_cluster(devices_compute_units, xbutil_dump_json, selected_cluster,
                         refresh_host):
    global auto_refresh_host_idx, auto_refresh_sheet_row

    last_udpated = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    for i_dn in range(len(devices_compute_units['device_id_names'])):
        #refresh_host = 'host' + str(i_dn)
        device_id_name = devices_compute_units['device_id_names'][i_dn]
        xbutil_top.generate_top_dict(xbutil_dump_json, refresh_host, device_id_name)
        xbutil_plot.update_history(xbutil_dump_json, refresh_host, device_id_name)
        if len(devices_compute_units['compute_units'][i_dn]) > 0:
            for cu in devices_compute_units['compute_units'][i_dn]:
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_HOST_COL, refresh_host)
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_DEVICE_COL, device_id_name)
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_COL, cu['name'])
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_STATUS_COL, cu['status'])
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_USAGE_COL, cu['usage'])
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_LAST_UPDATED_COL, last_udpated)
                auto_refresh_sheet_row = auto_refresh_sheet_row + 1
        else:
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_HOST_COL, refresh_host)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_DEVICE_COL, device_id_name)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_COL, 'None')
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_STATUS_COL, 'NA')
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_USAGE_COL, '')
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_LAST_UPDATED_COL, last_udpated)
            auto_refresh_sheet_row = auto_refresh_sheet_row + 1

    sheet_cluster.refresh()
    auto_refresh_host_idx = auto_refresh_host_idx + 1
    if auto_refresh_host_idx == len(clusters[combo_cluster['values'][selected_cluster]]):
        auto_refresh_host_idx = 0
        auto_refresh_sheet_row = 1


# get xbutil dump from each host in round robin fashion every XBUTIL_REFRESH_INTERVAL
def refresh_database(json_file):
    global auto_refresh_plot_seconds

    selected_cluster = combo_cluster.current()
    refresh_host = clusters[combo_cluster['values'][selected_cluster]][auto_refresh_host_idx]
    xbutil_dump_json = get_xbutil_dump(json_file, host=refresh_host)

    if xbutil_dump_json is not None:
        devices_compute_units = get_devices_compute_units(xbutil_dump_json)
        update_sheet_cluster(devices_compute_units, xbutil_dump_json,
                             selected_cluster, refresh_host)
        xbutil_top.show_top_info()
        xbutil_plot.plot_metrics(auto_refresh_plot_seconds)

    # add refresh_database back to the eventloop
    auto_refresh_plot_seconds = auto_refresh_plot_seconds + DEFAULT_XBUTIL_REFRESH_INTERVAL
    root_window.after(DEFAULT_XBUTIL_REFRESH_INTERVAL*1000, refresh_database, json_file)



def main():
    global plot_metric, prev_cluster_name, clusters, auto_refresh_host_idx, \
           auto_refresh_sheet_row

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
    user_config_file = home + '/xbutil-gui-config.json'
    default_config_file = __resource_path__ / 'xbutil-gui-config.json'
    cluster_names = []
    if Path(user_config_file).exists():
        config_file = Path(user_config_file)
    elif default_config_file.exists():
        config_file = default_config_file

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

    root_window.after(DEFAULT_XBUTIL_REFRESH_INTERVAL*1000, refresh_database, args.json_file)
    root_window.mainloop()


if __name__ == '__main__':
    main()



