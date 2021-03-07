# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, Toplevel
from tksheet import Sheet
import subprocess
import os
import datetime

from xbutil_gui import VERSION, LABEL_WIDTH

SHEET_DEVICES_TOTAL_ROWS = 200
SHEET_DEVICES_TOTAL_COLS = 8
SHEET_DEVICES_HOST_COL = 0
SHEET_DEVICES_PCIE_BDF_COL = 1
SHEET_DEVICES_DEVICE_COL = 2
SHEET_DEVICES_PCIE_CAP_SPEED_COL = 3
SHEET_DEVICES_PCIE_STA_SPEED_COL = 4
SHEET_DEVICES_PCIE_CAP_WIDTH_COL = 5
SHEET_DEVICES_PCIE_STA_WIDTH_COL = 6
SHEET_DEVICES_PCIE_BW_COL = 7

class DeviceManager:
    def __init__(self):
        self.selected_cluster_name = None
        self.pcie_dict = {}
        self.alveo_spec_dict = None

        # members for GUI
        self.label_cluster_name = None
        self.window_devman = None
        self.sheet_devices = None
        self.button_flash = None
        self.button_validate = None

    def validate_devices(self):
        print('validate_devices')

    def flash_devices(self):
        host = 'host'
        password = '12345678'
        xbmgmt_cmd = ['echo', password, '|',
                      'sudo', '-S', '/opt/xilinx/xrt/bin/xbmgmt', 'flash', '--update',
                      '--shell', 'xilinx_u50_gen3x16_xdma_201920_3', '--force']
        command = ['ssh', host] + xbmgmt_cmd
        print(' '.join(command))
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for l in iter(lambda: p.stdout.readline(), b''):
            print(l)

        print('INFO: Completed flashing all devices')

    def get_devices(self, sudo_password, hosts):
        # first save the password to a file with permission 0o600 to be secure
        password_file = os.path.expanduser("~") + '/.xbutil-gui-tmp'
        with open(password_file, 'w') as fh:
            os.chmod(password_file, 0o600)
            fh.write(sudo_password)

        lspci_cmd = "sudo -S <<< $(cat ~/.xbutil-gui-tmp) lspci -d 10ee: -vv"
        self.pcie_dict = {}
        for host in hosts:
            self.pcie_dict[host] = {}
            if host == 'localhost':
                command = lspci_cmd
            else:
                command = ['ssh', host] + lspci_cmd

            print('INFO: run {} on host'.format(command, host))
            p = subprocess.Popen(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, shell=True)
            lspci_out = p.stdout.read().decode('utf-8')
            lspci_lines = lspci_out.split('\n')
            first_line = True
            is_function0 = False
            for line in lspci_lines:
                if line.strip() == "":
                    continue

                if first_line and line.startswith('Password:'):
                    line = line[len('Password:'):]
                    first_line = False

                if not line[0].isspace():
                    fields = line.split()
                    pcie_bdf = fields[0]
                    if pcie_bdf[-1] == '0':
                        is_function0 = True
                        device_id = fields[-1]
                        self.pcie_dict[host][pcie_bdf] = {'device_id': device_id}
                    else:
                        is_function0 = False
                elif is_function0:
                    fields = line.split()
                    if fields[0] == 'LnkCap:':
                        self.pcie_dict[host][pcie_bdf]['LnkCapSpeed'] = fields[4][:-1]
                        self.pcie_dict[host][pcie_bdf]['LncCapWidth'] = fields[6][:-1]
                    elif fields[0] == 'LnkSta:':
                        self.pcie_dict[host][pcie_bdf]['LnkStaSpeed'] = fields[2][:-1]
                        self.pcie_dict[host][pcie_bdf]['LncStaWidth'] = fields[4][:-1]

            # finished processing all lines

        # finished processing all hosts
        self.display_devices()

    def display_devices(self):
        row = 1
        for host in self.pcie_dict.keys():
            for bdf in self.pcie_dict[host].keys():
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_HOST_COL, host)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_BDF_COL, bdf)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_DEVICE_COL,
                    self.alveo_spec_dict['pcie_device_ids'][self.pcie_dict[host][bdf]['device_id']])
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_CAP_SPEED_COL,
                                                 self.pcie_dict[host][bdf]['LnkCapSpeed'])
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_STA_SPEED_COL,
                                                 self.pcie_dict[host][bdf]['LnkStaSpeed'])
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_CAP_WIDTH_COL,
                                                 self.pcie_dict[host][bdf]['LncCapWidth'])
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_STA_WIDTH_COL,
                                                 self.pcie_dict[host][bdf]['LncStaWidth'])
                row = row + 1

    def show_devman_window(self, root_window, cluster_name):
        self.selected_cluster_name = cluster_name
        if self.window_devman is not None and tk.Toplevel.winfo_exists(self.window_devman):
            self.label_cluster_name['text'] = self.selected_cluster_name
            return

        self.window_devman = Toplevel(root_window)
        self.window_devman.title('xbutil GUI ' + VERSION + ' - Device Manager')
        self.window_devman.geometry('1200x400+20+200')
        # auto resize the row for sheet
        self.window_devman.grid_rowconfigure(1, weight=1)
        self.window_devman.columnconfigure(0, weight=0, minsize=150)
        self.window_devman.columnconfigure(1, weight=0, minsize=150)
        self.window_devman.columnconfigure(2, weight=0, minsize=150)
        self.window_devman.columnconfigure(3, weight=0, minsize=150)
        self.window_devman.columnconfigure(4, weight=0, minsize=150)
        self.window_devman.columnconfigure(5, weight=1, minsize=150)

        cur_grid_row = 0
        label_cluster = ttk.Label(self.window_devman, text="Cluster:",
                                  width=LABEL_WIDTH, anchor='e')
        label_cluster.grid(row=cur_grid_row, column=0, sticky='e')
        self.label_cluster_name = ttk.Label(self.window_devman,
                                            text=self.selected_cluster_name,
                                            width=40, anchor='w')
        self.label_cluster_name.grid(row=cur_grid_row, column=1, sticky='w')
        cur_grid_row = cur_grid_row + 1

        # sheet for all devices
        self.sheet_devices = Sheet(self.window_devman,
                              default_row_index="numbers",
                              total_rows=SHEET_DEVICES_TOTAL_ROWS,
                              total_columns=SHEET_DEVICES_TOTAL_COLS
                              )
        self.sheet_devices.enable_bindings(("single_select",  # "single_select" or "toggle_select"
                                       "drag_select",  # enables shift click selection as well
                                       "column_drag_and_drop",
                                       "row_drag_and_drop",
                                       "row_select",
                                       "column_width_resize",
                                       "double_click_column_resize",
                                       "arrowkeys",
                                       "right_click_popup_menu",
                                       "rc_select",
                                       "copy",
                                       "cut",
                                       "paste",
                                       "delete",
                                       "undo",
                                       "edit_cell"))
        self.sheet_devices.grid(row=cur_grid_row, columnspan=6, sticky='nswe')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_HOST_COL, 'Host')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_BDF_COL, 'PCIe BDF')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_DEVICE_COL, 'Device')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_CAP_SPEED_COL, 'LnkCap Speed')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_STA_SPEED_COL, 'LnkSta Speed')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_CAP_WIDTH_COL, 'LnkCap Width')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_STA_WIDTH_COL, 'LnkSta Width')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_BW_COL, 'PCIe BW(GB/s)')
        self.sheet_devices.column_width(column=SHEET_DEVICES_HOST_COL, width=150)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_BDF_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_DEVICE_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_CAP_SPEED_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_STA_SPEED_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_CAP_WIDTH_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_STA_WIDTH_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_BW_COL, width=100)
        cur_grid_row = cur_grid_row + 1

        self.button_validate = ttk.Button(self.window_devman, text="Validate",
                                          command=self.validate_devices)
        self.button_validate.grid(row=cur_grid_row, column=1, pady=10)
        self.button_flash = ttk.Button(self.window_devman, text="Flash",
                                       command=self.flash_devices)
        self.button_flash.grid(row=cur_grid_row, column=2, pady=10)



