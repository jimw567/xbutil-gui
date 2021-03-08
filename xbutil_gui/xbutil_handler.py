# -*- coding: utf-8 -*-
# xbutil GUI xbutil Command Handler Module
# Developers: Jim Wu, Annie Ren
# MIT License
# Copyright (c) 2020-2021 xbutil GUI Developers

import subprocess
import json
from xbutil_gui import CU_STATUS_DICT


def get_lspci(host='localhost'):
    lspci_cmd = ['lspci', '-d', '10ee:']
    if host == 'localhost':
        command = lspci_cmd
    else:
        command = ['ssh', host] + lspci_cmd
                   
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    lspci_out = p.stdout.read().decode('utf-8')
    lspci_lines = lspci_out.strip().split('\n')
    lspci_dict = {}
    for l in lspci_lines:
        fields = l.split()
        if len(fields) == 0:
            lspci_dict['NA'] = 'NA'
            break
        device_id = fields[0]
        device_xil_id = fields[-1]
        lspci_dict[device_id] = device_xil_id

    return lspci_dict

def get_xbutil_dump(json_file, host='localhost'):
    xbutil_dump_json = None
    lspci_dict = None
    if json_file is None:
        if host == 'localhost':
            command = ['/opt/xilinx/xrt/bin/unwrapped/xbutil2', 'examine', 
                       '--format', 'JSON', '--report', 'all']
        else:
            command = ['ssh', host, 
                       '/opt/xilinx/xrt/bin/unwrapped/xbutil2', 'examine', 
                       '--format', 'JSON', '--report', 'all']

        #print(' '.join(command))
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        xbutil_dump = p.stdout.read()
        try:
            xbutil_dump_json = json.loads(xbutil_dump.decode('utf-8'))
        except json.decoder.JSONDecodeError:
            # xbutil error. maybe card not installed/configured. try lspci
            #print('ERROR: cannot decode json from host', xbutil_dump)
            lspci_dict = get_lspci(host)
            xbutil_dump_json = None
    else:
        with open(json_file, 'r') as fp:
            xbutil_dump_json = json.load(fp)

    return xbutil_dump_json,lspci_dict


def get_devices_compute_units(xbutil_dump_json):
    devices_compute_units = {}
    device_id_names = []
    device_vbnvs = []
    device_ids = []
    compute_units = []
    
    if xbutil_dump_json is None:
        return []

    tmp_devices_vbnvs = {}
    for d in xbutil_dump_json['system']['host']['devices']:
        tmp_devices_vbnvs[d['bdf']] = d['vbnv']

    for d in xbutil_dump_json['devices']:
        device_id = d['device_id']
        device_vbnv = tmp_devices_vbnvs[device_id]
        device_ids.append(device_id)
        device_vbnvs.append(device_vbnv)
        device_id_names.append(device_id + '::' + device_vbnv)
        cur_cu = []
        if isinstance(d['compute_units'], list):
            for cu in d['compute_units']:
                cur_cu.append({'name': cu['name'], 'usage': cu['usage'],
                               'status': CU_STATUS_DICT.get(cu['status']['bit_mask'],
                                                            cu['status']['bit_mask'])})
        else:
            cur_cu.append({'name': 'NA', 'usage': '-', 'status': '-'})

        compute_units.append(cur_cu)

    devices_compute_units['device_ids'] = device_ids
    devices_compute_units['device_vbnvs'] = device_vbnvs
    devices_compute_units['device_id_names'] = device_id_names
    devices_compute_units['compute_units'] = compute_units

    return devices_compute_units


def get_devices_from_lspci(lspci_dict, alveo_spec_dict):
    devices_compute_units = {}
    device_id_names = []
    device_vbnvs = []
    device_ids = []
    compute_units = []

    for k in lspci_dict.keys():
        device_vbnv = alveo_spec_dict['pcie_device_ids'].get(lspci_dict[k], 'NA')
        device_ids.append(k)
        device_vbnvs.append(device_vbnv)
        device_id_names.append(k + "::" + device_vbnv)
        compute_units.append([{'name': 'NA', 'usage': '-', 'status': '-'}])
    
    devices_compute_units['device_ids'] = device_ids
    devices_compute_units['device_vbnvs'] = device_vbnvs
    devices_compute_units['device_id_names'] = device_id_names
    devices_compute_units['compute_units'] = compute_units


    return devices_compute_units