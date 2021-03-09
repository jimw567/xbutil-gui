# -*- coding: utf-8 -*-
# xbutil GUI Device Manager Module
# Developers: Jim Wu, Annie Ren
# MIT License
# Copyright (c) 2020-2021 xbutil GUI Developers

import tkinter as tk
from tkinter import ttk, Toplevel, scrolledtext, messagebox
from tksheet import Sheet
import subprocess
import os
import datetime
import re

from xbutil_gui import VERSION, LABEL_WIDTH

SHEET_DEVICES_TOTAL_ROWS = 200
SHEET_DEVICES_TOTAL_COLS = 9
SHEET_DEVICES_HOST_COL = 0
SHEET_DEVICES_PCIE_BDF_COL = 1
SHEET_DEVICES_DEVICE_COL = 2
SHEET_DEVICES_PCIE_CAP_SPEED_COL = 3
SHEET_DEVICES_PCIE_STA_SPEED_COL = 4
SHEET_DEVICES_PCIE_CAP_WIDTH_COL = 5
SHEET_DEVICES_PCIE_STA_WIDTH_COL = 6
SHEET_DEVICES_PCIE_WR_BW_COL = 7
SHEET_DEVICES_PCIE_RD_BW_COL = 8


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
        self.sheet_last_row = 1
        self.sheet_data_shadow = [{}] * SHEET_DEVICES_TOTAL_ROWS
        self.root_window_pointer = None
        self.window_log = None


    def validate_devices(self):
        # create a log widget if needed
        if self.window_log is None or not tk.Toplevel.winfo_exists(self.window_log):
            self.window_log = Toplevel(self.root_window_pointer)
            self.window_log.title('xbutil GUI ' + VERSION + ' - validate log')
            self.window_log.geometry('800x500+800+350')
            self.window_log.rowconfigure(0, weight=1)
            self.window_log.columnconfigure(0, weight=1)
            cur_grid_row = 0

            self.text_log = scrolledtext.ScrolledText(self.window_log)
            self.text_log.grid(row=cur_grid_row, column=0, sticky='nsew')
            self.text_log.update_idletasks()

        re_ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        re_pcie_wrbw = re.compile('FPGA write bandwidth =\s+(.*) MB')
        re_pcie_rdbw = re.compile('FPGA read bandwidth =\s+(.*) MB')
        re_platform = re.compile('Platform\s+:\s+(.*)')
        dash_line = '-' * 60 + '\n'
        for row in range(1, self.sheet_last_row):
            host = self.sheet_data_shadow[row]['host']
            bdf = self.sheet_data_shadow[row]['bdf']
            self.text_log.insert(tk.END, dash_line)
            self.text_log.insert(tk.END, 'Validating device ' + bdf + \
                                         ' on host ' + host + '\n')
            self.text_log.insert(tk.END, dash_line)

            xbutil_command = '/opt/xilinx/xrt/bin/xbutil --new validate -d ' + bdf
            if host == 'localhost':
                command = xbutil_command
            else:
                command = 'ssh ' + host + ' ' + xbutil_command

            p = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                 stderr=subprocess.STDOUT, shell=True)
            for line in iter(lambda: p.stdout.readline(), b''):
                # print(line.decode('utf-8'))
                line = re_ansi_escape.sub('', line.decode('utf-8'))
                m = re_pcie_wrbw.search(line)
                if m:
                    self.pcie_dict[host][bdf]['pcie_wrbw'] = float(m.group(1))/1000
                m = re_pcie_rdbw.search(line)
                if m:
                    self.pcie_dict[host][bdf]['pcie_rdbw'] = float(m.group(1))/1000
                m = re_platform.search(line)
                if m:
                    self.pcie_dict[host][bdf]['device'] = m.group(1)

                self.text_log.insert(tk.END, line)
                self.text_log.yview(tk.END)
                self.text_log.update_idletasks()

            # finished current bdf. Update metrics
            self.text_log.insert(tk.END, dash_line)
            self.text_log.insert(tk.END, 'Completed validating ' + bdf + \
                                         ' on host' + host + '\n')
            self.text_log.insert(tk.END, dash_line)

            self.sheet_devices.set_cell_data(row, SHEET_DEVICES_DEVICE_COL,
                self.pcie_dict[host][bdf]['device'])
            self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_WR_BW_COL,
                '{:.2f}'.format(self.pcie_dict[host][bdf]['pcie_wrbw']))
            self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_RD_BW_COL,
                '{:.2f}'.format(self.pcie_dict[host][bdf]['pcie_rdbw']))
            self.sheet_devices.refresh()

        # finished all bdfs
        self.text_log.insert(tk.END, dash_line)
        self.text_log.insert(tk.END, 'Completed validating ' + str(self.sheet_last_row-1) +
                                     ' devices\n')
        self.text_log.insert(tk.END, dash_line)
        self.text_log.yview(tk.END)
        self.text_log.update_idletasks()

    def flash_devices(self):
        messagebox.showinfo("showinfo", "Coming soon")
        # host = 'host'
        # password = '12345678'
        # xbmgmt_cmd = ['echo', password, '|',
        #               'sudo', '-S', '/opt/xilinx/xrt/bin/xbmgmt', 'flash', '--update',
        #               '--shell', 'xilinx_u50_gen3x16_xdma_201920_3', '--force']
        # command = ['ssh', host] + xbmgmt_cmd
        # print(' '.join(command))
        # p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # for l in iter(lambda: p.stdout.readline(), b''):
        #     print(l)
        #
        # print('INFO: Completed flashing all devices')

    def get_devices(self, hosts):

        self.pcie_dict = {}
        for host in hosts:
            self.pcie_dict[host] = {}
            if host == 'localhost':
                command = 'bash -c \"sudo -S <<< $(cat ~/.xbutil-gui-tmp) lspci -d 10ee: -vv\"'
            else:
                command = 'ssh ' + host + \
                          ' bash -l -c \\"sudo -S <<< $(cat ~/.xbutil-gui-tmp) lspci -d 10ee: -vv\\"'

            print('INFO: run {} on host {}'.format(command, host))
            p = subprocess.Popen(command, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, shell=True)
            lspci_out = p.stdout.read().decode('utf-8')
            p_returncode = p.wait()
            print('p_returncode=', p_returncode)
            if p_returncode != 0:
                print(lspci_out)

            lspci_lines = lspci_out.split('\n')
            is_function1 = False
            for line in lspci_lines:
                if line.strip() == "":
                    continue

                if not line[0].isspace():
                    fields = line.split()
                    bdf = fields[0]
                    if bdf[-1] == '1':
                        is_function1 = True
                        device_id = fields[-1]
                        self.pcie_dict[host][bdf] = {
                            'device_id': device_id,
                            'device': self.alveo_spec_dict['pcie_device_ids'][device_id],
                            'pcie_wrbw': '--',
                            'pcie_rdbw': '--'}
                    else:
                        is_function1 = False
                elif is_function1:
                    fields = line.split()
                    if fields[0] == 'LnkCap:':
                        self.pcie_dict[host][bdf]['LnkCapSpeed'] = fields[4][:-1]
                        self.pcie_dict[host][bdf]['LnkCapWidth'] = fields[6][:-1]
                    elif fields[0] == 'LnkSta:':
                        self.pcie_dict[host][bdf]['LnkStaSpeed'] = fields[2][:-1]
                        self.pcie_dict[host][bdf]['LnkStaWidth'] = fields[4][:-1]

            # finished processing all lines

        # finished processing all hosts
        self.display_devices()

    def display_devices(self):
        row = 1
        for host in self.pcie_dict.keys():
            for bdf in self.pcie_dict[host].keys():
                lnkcap_speed = self.pcie_dict[host][bdf]['LnkCapSpeed']
                lnksta_speed = self.pcie_dict[host][bdf]['LnkStaSpeed']
                lnkcap_width = self.pcie_dict[host][bdf]['LnkCapWidth']
                lnksta_width = self.pcie_dict[host][bdf]['LnkStaWidth']
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_HOST_COL, host)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_BDF_COL, bdf)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_DEVICE_COL,
                                                 self.pcie_dict[host][bdf]['device'])
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_CAP_SPEED_COL, lnkcap_speed)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_STA_SPEED_COL, lnksta_speed)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_CAP_WIDTH_COL, lnkcap_width)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_STA_WIDTH_COL, lnksta_width)
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_WR_BW_COL,
                                                 self.pcie_dict[host][bdf]['pcie_wrbw'])
                self.sheet_devices.set_cell_data(row, SHEET_DEVICES_PCIE_RD_BW_COL,
                                                 self.pcie_dict[host][bdf]['pcie_rdbw'])

                if lnkcap_speed != lnksta_speed:
                    self.sheet_devices.highlight_cells(row, SHEET_DEVICES_PCIE_STA_SPEED_COL, bg='red')
                if lnkcap_width != lnksta_width:
                    self.sheet_devices.highlight_cells(row, SHEET_DEVICES_PCIE_STA_WIDTH_COL, bg='red')

                self.sheet_data_shadow[row] = {'host': host, 'bdf': bdf}
                row = row + 1

        self.sheet_last_row = row

    def show_devman_window(self, root_window, cluster_name):
        self.selected_cluster_name = cluster_name
        if self.window_devman is not None and tk.Toplevel.winfo_exists(self.window_devman):
            self.label_cluster_name['text'] = self.selected_cluster_name
            return

        self.root_window_pointer = root_window
        self.window_devman = Toplevel(root_window)
        self.window_devman.title('xbutil GUI ' + VERSION + ' - Device Manager')
        self.window_devman.geometry('1200x400+20+150')
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
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_CAP_SPEED_COL, 'LnkCap Spd')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_STA_SPEED_COL, 'LnkSta Spd')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_CAP_WIDTH_COL, 'LnkCap xW')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_STA_WIDTH_COL, 'LnkSta xW')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_WR_BW_COL, 'PCIeWr GB/s')
        self.sheet_devices.set_cell_data(0, SHEET_DEVICES_PCIE_RD_BW_COL, 'PCIeRd GB/s')
        self.sheet_devices.column_width(column=SHEET_DEVICES_HOST_COL, width=150)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_BDF_COL, width=100)
        self.sheet_devices.column_width(column=SHEET_DEVICES_DEVICE_COL, width=250)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_CAP_SPEED_COL, width=75)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_STA_SPEED_COL, width=75)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_CAP_WIDTH_COL, width=75)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_STA_WIDTH_COL, width=75)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_WR_BW_COL, width=75)
        self.sheet_devices.column_width(column=SHEET_DEVICES_PCIE_RD_BW_COL, width=75)

        cur_grid_row = cur_grid_row + 1

        self.button_validate = ttk.Button(self.window_devman, text="Validate",
                                          command=self.validate_devices)
        self.button_validate.grid(row=cur_grid_row, column=1, pady=10)
        self.button_flash = ttk.Button(self.window_devman, text="Flash",
                                       command=self.flash_devices)
        self.button_flash.grid(row=cur_grid_row, column=2, pady=10)



