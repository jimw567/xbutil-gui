# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, Toplevel
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from pandas import DataFrame
import datetime

from xbutil_gui import VERSION, COMBO_WIDTH, LABEL_WIDTH, FIGURE_DPI, \
                       DEFAULT_XBUTIL_REFRESH_INTERVAL


class XbutilPlot:
    def __init__(self):
        self.selected_host = None
        self.selected_device_id_name = None
        self.selected_device_id = None

        # members for GUI
        self.label_host_name = None
        self.label_device_id_name = None
        self.window_plot = None
        self.combo_plot_metric = None
        self.combo_plot_auto_refresh = None
        self.figure_hist = None
        self.plot_hist = None
        self.plot_hist_twinx = None
        self.y_ax = None
        self.canvas_hist = None
        self.frame_toolbar = None
        self.toolbar_plot = None

        # members for plot data. each member if a dictionary of dictonary
        # {'host1-device-key1': {metric history},
        #  'host1-device-key2': {metric history},
        #  'host2-device-key1': {metric history}...}
        self.plot_metric = 'power/temperature'
        self.time_hist = {}
        self.power_hist = {}
        self.temp_hist = {}
        self.vccint_hist = {}
        self.iccint_hist = {}

    def plot_metrics(self, auto_refresh_seconds):
        if not (self.window_plot is not None and tk.Toplevel.winfo_exists(self.window_plot)):
            return

        selected_plot_metric = self.combo_plot_metric.get()
        if self.combo_plot_auto_refresh.get() == 'off':
            return
        auto_refresh_interval = int(self.combo_plot_auto_refresh.get())
        if selected_plot_metric != self.plot_metric:
            # always plot when selected metric is changed.
            pass
        elif auto_refresh_seconds % auto_refresh_interval > 0:
            return

        index_step = int(auto_refresh_interval/DEFAULT_XBUTIL_REFRESH_INTERVAL)
        host_device_key = self.selected_host + self.selected_device_id_name
        self.plot_metric = selected_plot_metric
        if len(self.power_hist[host_device_key][::index_step]) == 0:
            # nothing to plot yet
            return

        self.plot_hist.clear()
        if self.plot_hist_twinx is not None:
            self.plot_hist_twinx.clear()

        if self.plot_metric == 'power/temperature':
            y_hist_dict = {'time': self.time_hist[host_device_key][::index_step],
                           'power': self.power_hist[host_device_key][::index_step],
                           'temp': self.temp_hist[host_device_key][::index_step]}
            y_hist_df = DataFrame(y_hist_dict, columns=['time', 'power', 'temp'])
            y_hist_df.plot(kind='line', legend=True, x='time', y='power',
                           ax=self.plot_hist, color='r', marker='.', fontsize=10)
            self.plot_hist_twinx = y_hist_df['temp'].plot(
                kind='line', legend=True, ax=self.plot_hist,
                color='b', marker='.', fontsize=10, secondary_y=True)
            self.plot_hist.set_ylabel('Power(W)')
            self.plot_hist.right_ax.set_ylabel('Temperature (C)')
            self.plot_hist.set_title('Power(w)/Temperature(C) History')
            self.canvas_hist.draw()
        elif self.plot_metric == 'vccint/iccint':
            y_hist_dict = {'time': self.time_hist[host_device_key][::index_step],
                           'vccint': self.vccint_hist[host_device_key][::index_step],
                           'iccint': self.iccint_hist[host_device_key][::index_step]}
            y_hist_df = DataFrame(y_hist_dict, columns=['time', 'vccint', 'iccint'])
            y_hist_df.plot(kind='line', legend=True, x='time', y='vccint', ax=self.plot_hist,
                           color='r', marker='.', fontsize=10)
            self.plot_hist_twinx = y_hist_df['iccint'].plot(
                kind='line', legend=True, ax=self.plot_hist,
                color='b', marker='.', fontsize=10, secondary_y=True)
            self.plot_hist.set_ylabel('Vccint(V)')
            self.plot_hist.right_ax.set_ylabel('Iccint(A)')
            self.plot_hist.set_title('Vccint(V)/Iccint(A) History')
            self.canvas_hist.draw()

    def show_plot_window(self, root_window, selected_host, selected_device_id_name):
        self.selected_host = selected_host
        self.selected_device_id_name = selected_device_id_name
        self.selected_device_id = selected_device_id_name.split('::')[0]

        if self.window_plot is not None and tk.Toplevel.winfo_exists(self.window_plot):
            self.label_host_name['text'] = selected_host
            #self.label_host_name['text'] = 'host1'  # for documentation purpose
            self.label_device_id_name['text'] = selected_device_id_name
            return

        self.window_plot = Toplevel(root_window)
        self.window_plot.title('xbutil GUI ' + VERSION + ' - plot')

        cur_grid_row = 0
        label_host = ttk.Label(self.window_plot, text="Host", width=LABEL_WIDTH, anchor='e')
        label_host.grid(row=cur_grid_row, column=0, sticky='e')
        self.label_host_name = ttk.Label(self.window_plot, text=selected_host, width=40, anchor='w')
        self.label_host_name.grid(row=cur_grid_row, column=1, sticky='w')
        cur_grid_row = cur_grid_row + 1

        label_device = ttk.Label(self.window_plot, text="Device", width=LABEL_WIDTH, anchor='e')
        label_device.grid(row=cur_grid_row, column=0, sticky='e')
        self.label_device_id_name = ttk.Label(self.window_plot, text=selected_device_id_name, width=40, anchor='w')
        self.label_device_id_name.grid(row=cur_grid_row, column=1, sticky='w')
        cur_grid_row = cur_grid_row + 1

        # Add a dropdown list for plot metric
        lable_plot_metric = ttk.Label(self.window_plot, text="Plot metric").grid(
            row=cur_grid_row, column=0, sticky='e')
        self.combo_plot_metric = ttk.Combobox(self.window_plot, width=COMBO_WIDTH)
        self.combo_plot_metric['values'] = ('power/temperature', 'vccint/iccint')
        self.combo_plot_metric.grid(row=cur_grid_row, column=1, sticky='w')
        cur_grid_row = cur_grid_row + 1
        self.combo_plot_metric.current(0)

        # Auto refresh dropdown
        label_plot_auto_refresh = ttk.Label(self.window_plot, text="Auto Refresh interval(s)").grid(
            row=cur_grid_row, column=0, sticky='e')
        self.combo_plot_auto_refresh = ttk.Combobox(self.window_plot, width=COMBO_WIDTH)
        self.combo_plot_auto_refresh['values'] = ('off', '10', '60')
        self.combo_plot_auto_refresh.grid(row=cur_grid_row, column=1, sticky='w')
        self.combo_plot_auto_refresh.current(1)
        cur_grid_row = cur_grid_row + 1

        # plot row
        self.figure_hist = plt.Figure(figsize=(10, 5), dpi=FIGURE_DPI)
        self.plot_hist = self.figure_hist.add_subplot(111)
        self.canvas_hist = FigureCanvasTkAgg(self.figure_hist, self.window_plot)
        self.canvas_hist.get_tk_widget().grid(row=cur_grid_row, columnspan=4, sticky='nsew')
        cur_grid_row = cur_grid_row + 1

        # Plot navigation toolbar
        self.frame_toolbar = tk.Frame(self.window_plot)
        self.frame_toolbar.grid(row=cur_grid_row, columnspan=4)
        self.toolbar_plot = NavigationToolbar2Tk(self.canvas_hist, self.frame_toolbar)
        cur_grid_row = cur_grid_row + 1

    def update_history(self, xbutil_dump_json, host, device_id_name):
        host_device_key = host + device_id_name
        device_id = device_id_name.split('::')[0]
        if self.time_hist.get(host_device_key) is None:
            self.time_hist[host_device_key] = []
            self.power_hist[host_device_key] = []
            self.temp_hist[host_device_key] = []
            self.vccint_hist[host_device_key] = []
            self.iccint_hist[host_device_key] = []

        fpga_present = False
        for dev in xbutil_dump_json['devices']:
            if dev['device_id'] != device_id:
                continue

            for t in dev['thermals']:
                if t['location_id'] == 'fpga0' and t['is_present']:
                    fpga_present = True
                    fpga_temp = float(t['temp_C'])

        if not fpga_present:
            return

        self.time_hist[host_device_key].append(datetime.datetime.now().strftime("%m/%d %H:%M"))
        self.temp_hist[host_device_key].append(fpga_temp)

        for dev in xbutil_dump_json['devices']:
            if dev['device_id'] != device_id:
                continue

            self.power_hist[host_device_key].append(float(dev['electrical']['power_consumption_watts']))
            for pr in dev['electrical']['power_rails']:
                if pr['id'] == 'vccint':
                    self.vccint_hist[host_device_key].append(float(pr['voltage']['volts']))
                    self.iccint_hist[host_device_key].append(float(pr['current']['amps']))
