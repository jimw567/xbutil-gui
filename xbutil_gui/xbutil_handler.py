# -*- coding: utf-8 -*-

import subprocess
import json
from xbutil_gui import CU_STATUS_DICT


def get_xbutil_dump(json_file, host='localhost'):
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
            print('ERROR: cannot decode json', xbutil_dump)
            xbutil_dump_json = None
    else:
        with open(json_file, 'r') as fp:
            xbutil_dump_json = json.load(fp)

    return xbutil_dump_json


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

