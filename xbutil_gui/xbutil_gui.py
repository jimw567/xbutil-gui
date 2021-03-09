# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from tksheet import Sheet
import subprocess
import os
import json
import shutil
import datetime
import argparse
from pathlib import Path
import socket

from xbutil_gui.xbutil_top import XbutilTop
from xbutil_gui.plot_metrics import PlotMetrics
from xbutil_gui.device_manager import DeviceManager
from xbutil_gui.xbutil_handler import get_devices_compute_units, \
                                      get_xbutil_dump, get_devices_from_lspci
from xbutil_gui import VERSION, LABEL_WIDTH, COMBO_WIDTH, STATUS_CODES, \
                DEFAULT_XBUTIL_REFRESH_INTERVAL, __resource_path__, __icon__, \
                SHEET_TOTAL_ROWS, SHEET_TOTAL_COLS,  \
                SHEET_HOST_COL, SHEET_DEVICE_COL, SHEET_CU_COL, SHEET_CU_STATUS_COL, \
                SHEET_CU_USAGE_COL, SHEET_POWER_COL, SHEET_TEMP_COL, \
                SHEET_LAST_UPDATED_COL


# interval in seconds between xbutil json dumps
auto_refresh_plot_seconds = 0
xbutil_top = XbutilTop()
plot_metrics = PlotMetrics()
device_manager = DeviceManager()

shadow_sheet_hosts = ['' for i in range(SHEET_TOTAL_ROWS)]
shadow_sheet_device_id_names = ['' for i in range(SHEET_TOTAL_ROWS)]
pause_sheet = 0
no_supassword = False


def get_selected_host_device():
    global shadow_sheet_hosts, shadow_sheet_device_id_names

    sheet_selected = sheet_cluster.get_currently_selected()
    if len(sheet_selected) == 0:
        messagebox.showinfo("showinfo", "Please select a cell or row on the sheet first.")
        return -1, None, None

    if str(sheet_selected[0]) == 'row':
        selected_row = sheet_selected[1]
    else:
        selected_row = sheet_selected[0]

    selected_host = shadow_sheet_hosts[selected_row]
    selected_device_id_name = shadow_sheet_device_id_names[selected_row]
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

    plot_metrics.show_plot_window(root_window, selected_host, selected_device_id_name)

def show_devman_window():
    if not no_sudo_passwd:
        sudo_password = tk.simpledialog.askstring("Password", "Enter Sudo password:", show='*')
        if sudo_password is None or sudo_password == '':
            return

        # Save the password to a file with permission 0o600 to be secure
        password_file = os.path.expanduser("~") + '/.xbutil-gui-tmp'
        with open(password_file, 'w') as fh:
            os.chmod(password_file, 0o600)
            fh.write(sudo_password)

    selected_cluster = combo_cluster.current()
    selected_cluster_name = combo_cluster['values'][selected_cluster]

    device_manager.show_devman_window(root_window, selected_cluster_name)
    device_manager.get_devices(clusters[selected_cluster_name])


def toggle_pause_sheet():
    global pause_sheet
    if pause_sheet == 0:
        pause_sheet = 1
        button_pause_sheet['text'] = 'Resume'
    else:
        pause_sheet = 0
        button_pause_sheet['text'] = 'Pause'


###############################################################################
# root window
###############################################################################
running_host = socket.gethostname()
root_window = tk.Tk()
root_window.geometry('1500x700+20+20')
root_window.title('Xilinx xbutil GUI ' + VERSION + ' runnning on ' + running_host)
root_window_icon = tk.PhotoImage(file=str(__icon__))
root_window.iconphoto(True, root_window_icon)
root_window.columnconfigure(0, weight=0, minsize=150)
root_window.columnconfigure(1, weight=0, minsize=150)
root_window.columnconfigure(2, weight=0, minsize=150)
root_window.columnconfigure(3, weight=0, minsize=150)
root_window.columnconfigure(4, weight=0, minsize=150)
root_window.columnconfigure(5, weight=1, minsize=150)

cur_grid_row = 0
label_cluster = ttk.Label(root_window, text="Cluster", width=LABEL_WIDTH, anchor='w')
label_cluster.grid(row=cur_grid_row, column=0,  sticky='w', pady=10)
combo_cluster = ttk.Combobox(root_window, width=COMBO_WIDTH)
combo_cluster['values'] = []
combo_cluster.grid(row=cur_grid_row, column=1, columnspan=3, sticky='w', pady=10)
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
sheet_cluster.grid(row=cur_grid_row, columnspan=6, sticky='nswe')
root_window.grid_rowconfigure(cur_grid_row, weight=1)
sheet_cluster.set_cell_data(0, SHEET_HOST_COL, 'Host')
sheet_cluster.set_cell_data(0, SHEET_DEVICE_COL, 'Device ID::Shell')
sheet_cluster.set_cell_data(0, SHEET_CU_COL, 'Compute Unit (CU)')
sheet_cluster.set_cell_data(0, SHEET_CU_STATUS_COL, 'CU Status')
sheet_cluster.set_cell_data(0, SHEET_CU_USAGE_COL, 'CU Usage')
sheet_cluster.set_cell_data(0, SHEET_POWER_COL, 'P(W)')
sheet_cluster.set_cell_data(0, SHEET_TEMP_COL, 'T(C)')
sheet_cluster.set_cell_data(0, SHEET_LAST_UPDATED_COL, 'Last Updated')
sheet_cluster.column_width(column=SHEET_HOST_COL, width=150)
sheet_cluster.column_width(column=SHEET_DEVICE_COL, width=300)
sheet_cluster.column_width(column=SHEET_CU_COL, width=300)
sheet_cluster.column_width(column=SHEET_CU_STATUS_COL, width=60)
sheet_cluster.column_width(column=SHEET_CU_USAGE_COL, width=60)
sheet_cluster.column_width(column=SHEET_POWER_COL, width=50)
sheet_cluster.column_width(column=SHEET_TEMP_COL, width=50)
sheet_cluster.column_width(column=SHEET_LAST_UPDATED_COL, width=200)
cur_grid_row = cur_grid_row + 1
sheet_cluster_last_row = 0

# command buttons for selected host
button_top = ttk.Button(root_window, text="Top", command=show_top_window)
button_top.grid(row=cur_grid_row, column=1, pady=10)

button_plot = ttk.Button(root_window, text="Plot", command=show_plot_window)
button_plot.grid(row=cur_grid_row, column=2, pady=10)

button_manage_devices = ttk.Button(root_window, text="Manage", command=show_devman_window)
button_manage_devices.grid(row=cur_grid_row, column=3, pady=10)

button_pause_sheet = ttk.Button(root_window, text="Pause", command=toggle_pause_sheet)
button_pause_sheet.grid(row=cur_grid_row, column=4, pady=10)
cur_grid_row = cur_grid_row + 1

# global variables
cur_cluster_name = ""
auto_refresh_host_idx = 0
auto_refresh_sheet_row = 0
alveo_spec_dict = {}


def update_sheet_cluster(devices_compute_units, xbutil_dump_json, selected_cluster,
                         refresh_host):
    global auto_refresh_host_idx, auto_refresh_sheet_row, sheet_cluster_last_row
    global shadow_sheet_hosts, shadow_sheet_hosts, alveo_spec_dict, pause_sheet

    if pause_sheet == 1:
        return

    host_displayed = 0
    last_udpated = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")

    for i_dn in range(len(devices_compute_units['device_id_names'])):
        #refresh_host = 'host' + str(i_dn)
        device_vbnv = devices_compute_units['device_vbnvs'][i_dn]
        device_id_name = devices_compute_units['device_id_names'][i_dn]
        last_metrics = plot_metrics.get_last_metrics(refresh_host, device_id_name)
        if xbutil_dump_json is not None:
            xbutil_top.generate_top_dict(xbutil_dump_json, refresh_host, device_id_name)
            plot_metrics.update_history(xbutil_dump_json, refresh_host, device_id_name)
        
        dev_displayed = 0
        for cu in devices_compute_units['compute_units'][i_dn]:
            if host_displayed == 0:
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_HOST_COL, refresh_host)
                sheet_cluster.highlight_rows([auto_refresh_sheet_row], bg='light sky blue' )
            else:
                sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_HOST_COL, '')
                sheet_cluster.dehighlight_rows([auto_refresh_sheet_row])

            host_displayed = 1

            if dev_displayed == 0:
                dev = device_id_name
                p_display = last_metrics[0]
                t_display = last_metrics[1]

                board = alveo_spec_dict["shell_board_lut"][device_vbnv]
                if t_display > alveo_spec_dict[board]['fpga_temp']['critical']:
                    sheet_cluster.highlight_cells(auto_refresh_sheet_row,
                                                  SHEET_TEMP_COL, bg='red')
                elif t_display > alveo_spec_dict[board]['fpga_temp']['warning']:
                    sheet_cluster.highlight_cells(auto_refresh_sheet_row,
                                                  SHEET_TEMP_COL, bg='yellow')
            else:
                dev = ''
                p_display = ''
                t_display = ''

            dev_displayed = 1
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_DEVICE_COL, dev)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_COL, cu['name'])
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_STATUS_COL, cu['status'])
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_CU_USAGE_COL, cu['usage'])
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_POWER_COL, p_display)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_TEMP_COL, t_display)
            sheet_cluster.set_cell_data(auto_refresh_sheet_row, SHEET_LAST_UPDATED_COL, last_udpated)
            # save host/dev_id_name into shadow varaibles
            shadow_sheet_hosts[auto_refresh_sheet_row] = refresh_host
            shadow_sheet_device_id_names[auto_refresh_sheet_row] = device_id_name
            auto_refresh_sheet_row = auto_refresh_sheet_row + 1


    sheet_cluster.refresh()
    auto_refresh_host_idx = auto_refresh_host_idx + 1
    if auto_refresh_host_idx == len(clusters[combo_cluster['values'][selected_cluster]]):
        auto_refresh_host_idx = 0
        
        if sheet_cluster_last_row > auto_refresh_sheet_row:
            # clear contents from previous full scan
            sheet_cluster.dehighlight_rows(range(auto_refresh_sheet_row, sheet_cluster_last_row+1))
            for r in range(auto_refresh_sheet_row, sheet_cluster_last_row+1):
                for c in range(SHEET_TOTAL_COLS):
                    sheet_cluster.set_cell_data(r, c, '')

        # udpate the last row count
        sheet_cluster_last_row = auto_refresh_sheet_row
        auto_refresh_sheet_row = 1


# get xbutil dump from each host in round robin fashion every XBUTIL_REFRESH_INTERVAL
def refresh_database(json_file):
    global auto_refresh_plot_seconds, auto_refresh_host_idx, cur_cluster_name, \
           auto_refresh_sheet_row, sheet_cluster_last_row

    selected_cluster = combo_cluster.current()
    selected_cluster_name = combo_cluster['values'][selected_cluster]
    if cur_cluster_name != selected_cluster_name:
        print('INFO: switch to new cluster', selected_cluster_name)
        auto_refresh_host_idx = 0
        auto_refresh_sheet_row = 1
        cur_cluster_name = selected_cluster_name
        sheet_cluster_last_row = SHEET_TOTAL_ROWS - 1

    refresh_host = clusters[selected_cluster_name][auto_refresh_host_idx]
    xbutil_dump_json,lspci_dict = get_xbutil_dump(json_file, host=refresh_host)

    if xbutil_dump_json is not None:
        devices_compute_units = get_devices_compute_units(xbutil_dump_json)
        update_sheet_cluster(devices_compute_units, xbutil_dump_json,
                             selected_cluster, refresh_host)
        xbutil_top.show_top_info()
        plot_metrics.plot_metrics(auto_refresh_plot_seconds)
    elif lspci_dict:
        devices_compute_units = get_devices_from_lspci(lspci_dict, alveo_spec_dict)
        update_sheet_cluster(devices_compute_units, xbutil_dump_json,
                             selected_cluster, refresh_host)
    else:
        # something wrong with current refresh host. Move on to the next host
        auto_refresh_host_idx = auto_refresh_host_idx + 1
        if auto_refresh_host_idx == len(clusters[selected_cluster_name]):
            auto_refresh_host_idx = 0

    # add refresh_database back to the eventloop
    auto_refresh_plot_seconds = auto_refresh_plot_seconds + DEFAULT_XBUTIL_REFRESH_INTERVAL
    root_window.after(DEFAULT_XBUTIL_REFRESH_INTERVAL*1000, refresh_database, json_file)


def main():
    global plot_metric, cur_cluster_name, clusters, auto_refresh_host_idx, \
           auto_refresh_sheet_row, alveo_spec_dict, no_sudo_passwd

    parser = argparse.ArgumentParser()
    parser.add_argument('--json-file', dest='json_file', default=None,
                        help='Specify a JSON file for getting the data')
    parser.add_argument('--no-sudo-passwd', action='store_true', dest='no_sudo_passwd', 
                        help='Do not prompt for sudo password')
    args = parser.parse_args()
    no_sudo_passwd = args.no_sudo_passwd

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

    alveo_spec_file = __resource_path__ / 'alveo-specifications.json'
    with open(alveo_spec_file, 'r') as fp:
        alveo_spec_dict = json.load(fp)

    device_manager.alveo_spec_dict = alveo_spec_dict

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
        cur_cluster_name = cluster_names[0]
        auto_refresh_host_idx = 0
        auto_refresh_sheet_row = 1

    root_window.after(DEFAULT_XBUTIL_REFRESH_INTERVAL*1000, refresh_database, args.json_file)
    root_window.mainloop()


if __name__ == '__main__':
    main()



