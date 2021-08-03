# -*- coding: utf-8 -*-
# xbutil GUI Top Module
# Developers: Jim Wu, Annie Ren
# MIT License
# Copyright (c) 2020-2021 xbutil GUI Developers

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
            self.top_dicts[host_device_key] = {'device_combo_name': device_id_name,
                                               'compute_units': {},
                                               'dma_metrics' : {}}

        if self.top_dicts[host_device_key].get('compute_units'):
            # save previous data
            for ba in self.top_dicts[host_device_key]['compute_units'].keys():
                self.top_dicts[host_device_key]['compute_units'][ba]['prev_usage'] = \
                    self.top_dicts[host_device_key]['compute_units'][ba]['usage']
                
            for ch in self.top_dicts[host_device_key]['dma_metrics'].keys():
                self.top_dicts[host_device_key]['dma_metrics'][ch]['prev_h2c'] = \
                    self.top_dicts[host_device_key]['dma_metrics'][ch]['h2c']
                self.top_dicts[host_device_key]['dma_metrics'][ch]['prev_c2h'] = \
                    self.top_dicts[host_device_key]['dma_metrics'][ch]['c2h']

        self.top_dicts[host_device_key]['device_memory'] = []
        self.top_dicts[host_device_key]['power'] = 0
        self.top_dicts[host_device_key]['last_updated'] = datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        for d in xbutil_dump_json['devices']:
            if d['device_id'] != self.selected_device_id:
                continue

            self.top_dicts[host_device_key]['power'] = d['electrical']['power_consumption_watts']

            # memory topology and usage information
            if d['mem_topology']['board'].get('memory') is not None:
                for m in d['mem_topology']['board']['memory']['memories']:
                    m_dict = {'tag': m['tag'], 'type': m['type'],
                              'temp': int(m['extended_info'].get('temperature_C', 0)),
                              'size': int(m['range_bytes'], 0) >> 20,
                              'usage': int(m['extended_info']['usage']['allocated_bytes'])}

                    self.top_dicts[host_device_key]['device_memory'].append(m_dict)

            # compute units
            cu_new_usage = False
            for c in d['compute_units']:
                ba = c['base_address']
                usage = int(c['usage'])
                if self.top_dicts[host_device_key]['compute_units'].get(ba):
                    self.top_dicts[host_device_key]['compute_units'][ba]['usage'] = usage
                else:
                    self.top_dicts[host_device_key]['compute_units'][ba] = {'usage': usage}

                prev_usage = self.top_dicts[host_device_key]['compute_units'][ba].get('prev_usage')
                if prev_usage and usage > prev_usage:
                    cu_new_usage = True
                    self.top_dicts[host_device_key]['compute_units'][ba]['last_usage'] = \
                        usage - prev_usage

            # DMA transfer metrics
            for t in d['mem_topology']['board']['direct_memory_accesses']['metrics']:
                ch = t['channel_id']
                h2c = int(t['host_to_card_bytes'], 0)
                c2h = int(t['card_to_host_bytes'], 0)
                if self.top_dicts[host_device_key]['dma_metrics'].get(ch):
                    self.top_dicts[host_device_key]['dma_metrics'][ch]['h2c'] = h2c
                    self.top_dicts[host_device_key]['dma_metrics'][ch]['c2h'] = c2h
                else:
                    self.top_dicts[host_device_key]['dma_metrics'][ch] = \
                        {'h2c': h2c, 'c2h': c2h}

                prev_h2c = self.top_dicts[host_device_key]['dma_metrics'][ch].get('prev_h2c')
                prev_c2h = self.top_dicts[host_device_key]['dma_metrics'][ch].get('prev_c2h')
                # only update once CU usage is recorded
                if cu_new_usage and prev_h2c and h2c > prev_h2c:
                    self.top_dicts[host_device_key]['dma_metrics'][ch]['last_h2c'] = \
                        h2c - prev_h2c
                if cu_new_usage and prev_c2h and c2h > prev_c2h:
                    self.top_dicts[host_device_key]['dma_metrics'][ch]['last_c2h'] = \
                        c2h - prev_c2h

    ###########################################################################
    # show top info
    ###########################################################################
    def show_top_info(self):
        if self.window_top is None or not tk.Toplevel.winfo_exists(self.window_top):
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
        MEM_INFO_FORMAT = '{0:12s}|{1:12s}|{2:<8d}|{3:<12d}|{4:>15s}'

        self.text_top.insert(tk.END,
                        MEM_INFO_HEADER_FORMAT.format('Tag', 'Type', 'Temp', 'Size(MB)', 'Usage'))
        self.text_top.insert(tk.END, '\n')

        for m in top_dict['device_memory']:
            m_usage = m['usage']
            self.text_top.insert(tk.END,
                MEM_INFO_FORMAT.format(m['tag'], m['type'], m['temp'], m['size'], f'{m_usage:,}'))
            self.text_top.insert(tk.END, '\n')

        self.text_top.insert(tk.END, '\nPower: ' + str(top_dict['power']) + 'W\n')

        self.text_top.insert(tk.END, '\nTotal DMA Transfer Metrics:\n')
        for ch in top_dict['dma_metrics'].keys():
            ch_m = top_dict['dma_metrics'][ch]
            h2c = ch_m['h2c']
            c2h = ch_m['c2h'] 
            self.text_top.insert(tk.END, 'Channel ' + ch + ': host to card ' + f'{h2c:,}' + '\n')
            self.text_top.insert(tk.END, 'Channel ' + ch + ': card to host ' + f'{c2h:,}' '\n')

        self.text_top.insert(tk.END, '\nCompute Unit Usage:\n')
        for ba in top_dict['compute_units'].keys():
            self.text_top.insert(tk.END, 'CU ' + ba + ': ' + 
                                         str(top_dict['compute_units'][ba]['usage']) + '\n')

        self.text_top.insert(tk.END, '\nLast Activity:\n')
        for ba in top_dict['compute_units'].keys():
            last_usage = self.top_dicts[host_device_key]['compute_units'][ba].get('last_usage')
            if last_usage:
                self.text_top.insert(tk.END, 'CU ' + ba + ': ' + str(last_usage) + '\n')

        for ch in top_dict['dma_metrics'].keys():
            last_h2c = top_dict['dma_metrics'][ch].get('last_h2c')
            if last_h2c:
                self.text_top.insert(tk.END, 'Channel ' + ch + ': host to card ' +
                            f'{last_h2c:,}' + '\n')
            last_c2h = top_dict['dma_metrics'][ch].get('last_c2h')
            if last_c2h:
                self.text_top.insert(tk.END, 'Channel ' + ch + ': card to host ' +
                            f'{last_c2h:,}' + '\n')

        self.text_top.yview(tk.END)

    ###########################################################################
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
            self.window_top.geometry('600x850+1000+200')

            cur_grid_row = 0

            self.text_top = scrolledtext.ScrolledText(self.window_top)
            #self.text_top.pack()
            self.text_top.grid(row=cur_grid_row, column=0, sticky='nsew')
            self.window_top.rowconfigure(cur_grid_row, weight=1)
            self.window_top.columnconfigure(0, weight=1)
