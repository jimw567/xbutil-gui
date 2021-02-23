# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import messagebox, Toplevel, scrolledtext
import datetime

from xbutil_gui import VERSION


class XbutilTop:
    def __init__(self):
        self.selected_host = None
        self.selected_device_id_name = None
        # top_dicts is a dictionary of dictionary
        # {'host1-device-key1': {top information dictionary for host1},
        #  'host1-device-key2': {top information dictionary for host2},
        #  'host2-device-key1': {top information dictionary for host2}...}
        self.top_dicts = {}
        self.selected_device_id = None
        self.window_top = None
        self.text_top = None

    def generate_top_dict(self, xbutil_dump_json, host, device_id_name):
        host_device_key = host + device_id_name
        if self.top_dicts.get(host_device_key) is None:
            self.top_dicts[host_device_key] = {}

        self.top_dicts[host_device_key] = {'device_combo_name': device_id_name}
        self.top_dicts[host_device_key]['device_memory'] = []
        self.top_dicts[host_device_key]['dma_metrics'] = []
        self.top_dicts[host_device_key]['compute_units'] = []
        self.top_dicts[host_device_key]['power'] = 0
        self.top_dicts[host_device_key]['last_updated'] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        for d in xbutil_dump_json['devices']:
            if d['device_id'] == self.selected_device_id:
                self.top_dicts[host_device_key]['power'] = d['electrical']['power_consumption_watts']

                # memory topology and usage information
                if d['mem_topology']['board'].get('memory') is not None:
                    for m in d['mem_topology']['board']['memory']['memories']:
                        m_dict = {'tag': m['tag'], 'type': m['type'],
                                  'temp': int(m['extended_info'].get('temperature_C', 0)),
                                  'size': int(m['range_bytes'], 0) >> 20,
                                  'usage': int(m['extended_info']['usage']['allocated_bytes'])}

                        self.top_dicts[host_device_key]['device_memory'].append(m_dict)

                # DMA transfer metrics
                for t in d['mem_topology']['board']['direct_memory_accesses']['metrics']:
                    t_dict = {'channel_id': t['channel_id'],
                              'host_to_card_bytes': int(t['host_to_card_bytes'], 0) >> 20,
                              'card_to_host_bytes': int(t['card_to_host_bytes'], 0) >> 20}

                    self.top_dicts[host_device_key]['dma_metrics'].append(t_dict)

                # compute units
                for c in d['compute_units']:
                    c_dict = {'base_address': c['base_address'], 'usage': c['usage']}
                    self.top_dicts[host_device_key]['compute_units'].append(c_dict)

    # show top info
    def show_top_info(self):
        if self.window_top is not None and tk.Toplevel.winfo_exists(self.window_top):
            pass
        else:
            return

        host_device_key = self.selected_host + self.selected_device_id_name
        if self.top_dicts.get(host_device_key) is None:
            self.text_top.delete('1.0', tk.END)
            self.text_top.insert(tk.END, 'No data is collected yet for host ' + self.selected_host)
            return

        top_dict = self.top_dicts[host_device_key]
        self.text_top.delete('1.0', tk.END)
        self.text_top.insert(tk.END, 'Last updated: ' + top_dict['last_updated'] + '\n')
        self.text_top.insert(tk.END, 'Host: ' + self.selected_host + '\n')
        self.text_top.insert(tk.END, 'Device: ' + top_dict['device_combo_name'] + '\n\n')

        self.text_top.insert(tk.END, 'Device Memory Usage:\n')
        MEM_INFO_HEADER_FORMAT = '{0:12s}|{1:12s}|{2:8s}|{3:12s}|{4:20s}'
        MEM_INFO_FORMAT = '{0:12s}|{1:12s}|{2:<8d}|{3:<12d}|{4:<20d}'

        self.text_top.insert(tk.END,
                        MEM_INFO_HEADER_FORMAT.format('Tag', 'Type', 'Temp', 'Size(MB)', 'Usage'))
        self.text_top.insert(tk.END, '\n')

        for m in top_dict['device_memory']:
            self.text_top.insert(tk.END,
                            MEM_INFO_FORMAT.format(m['tag'], m['type'], m['temp'], m['size'], m['usage']))
            self.text_top.insert(tk.END, '\n')

        self.text_top.insert(tk.END, '\nPower: ' + str(top_dict['power']) + 'W\n')

        self.text_top.insert(tk.END, '\nTotal DMA Transfer Metrics:\n')
        for m in top_dict['dma_metrics']:
            self.text_top.insert(tk.END, 'Channel ' + str(m['channel_id']) + ': host to card ' +
                            str(m['host_to_card_bytes']) + 'MB\n')
            self.text_top.insert(tk.END, 'Channel ' + str(m['channel_id']) + ': card to host ' +
                            str(m['card_to_host_bytes']) + 'MB\n')

        self.text_top.insert(tk.END, '\nCompute Unit Usage:\n')
        for c in top_dict['compute_units']:
            self.text_top.insert(tk.END, 'CU ' + c['base_address'] + ': ' + c['usage'] + '\n')

    def show_top_window(self, root_window, selected_host, selected_device_id_name):
        self.selected_host = selected_host
        self.selected_device_id_name = selected_device_id_name
        self.selected_device_id = selected_device_id_name.split('::')[0]

        if self.window_top is not None and tk.Toplevel.winfo_exists(self.window_top):
            return
        else:
            # create a new Toplevel
            self.window_top = Toplevel(root_window)
            self.window_top.title('xbutil GUI ' + VERSION + ' - top')
            self.text_top = scrolledtext.ScrolledText(self.window_top, width=100, height=40)
            self.text_top.pack()