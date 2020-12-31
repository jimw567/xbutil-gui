import tkinter as tk
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import subprocess
import json
import shutil
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
import argparse
import atexit

# global variables
status_codes = {
    'XRT_NOT_SETUP': {
        'code': 1,
        'message': 'ERROR: xbutil not found. Please set up XRT environment before running this application.'
    }
}
main_window = tk.Tk()
main_window.title('Xilinx xbutil GUI')
main_window_icon = tk.PhotoImage(file='resources/xbutil-icon.png')
main_window.iconphoto(True, main_window_icon)
figure_dpi = 100
figure_hist = plt.Figure(figsize=(10, 5), dpi=figure_dpi)
plot_hist = figure_hist.add_subplot(111)
canvas_hist = FigureCanvasTkAgg(figure_hist, main_window)
canvas_hist.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
plot_type = 'temp'  # valid values: power, temp, volt
time_hist = []
power_hist = []
temp_hist = []
refresh_interval = 10 # seconds between refresh
scheduler = BackgroundScheduler(daemon=True)


def get_xbutil_dump(json_file):
    timestamp = datetime.datetime.now()
    #print('DEBUG:', timestamp, 'get_xbutil_dump from', json_file)
    if json_file is None:
        command = ['xbutil', 'dump']
        p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        xbutil_dump = p.stdout.read()
        xbutil_dump_json = json.loads(xbutil_dump.decode('utf-8'))
    else:
        with open(json_file, 'r') as fp:
            xbutil_dump_json = json.load(fp)

    #time_hist.append(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    time_hist.append(timestamp.strftime("%m/%d %H:%M"))
    power_hist.append(int(xbutil_dump_json['board']['physical']['power']))
    temp_hist.append(float(xbutil_dump_json['board']['physical']['thermal']['fpga_temp']))


def animate_plot(iter):
    if iter % refresh_interval > 0:
        return

    if len(power_hist[::refresh_interval]) == 0:
        # nothing to plot yet
        return

    plot_hist.clear()
    if plot_type == 'power':
        y_hist_dict = {'time': time_hist[::refresh_interval], 'power': power_hist[::refresh_interval]}
        y_hist_df = DataFrame(y_hist_dict, columns=['time', 'power'])
        y_hist_df.plot(kind='line', legend=False, x='time', y='power', ax=plot_hist,
                       color='r', marker='.', fontsize=10)
        plot_hist.set_title('Power(w) History')
    elif plot_type == 'temp':
        y_hist_dict = {'time': time_hist[::refresh_interval], 'temp': temp_hist[::refresh_interval]}
        y_hist_df = DataFrame(y_hist_dict, columns=['time', 'temp'])
        y_hist_df.plot(kind='line', legend=False, x='time', y='temp', ax=plot_hist,
                       color='r', marker='.', fontsize=10)
        plot_hist.set_title('Temperature(C) History')


def xbutil_gui_main():
    global plot_type

    parser = argparse.ArgumentParser()
    parser.add_argument('--json-file', dest='json_file', default=None,
                        help='Specify a JSON file for getting the data')
    parser.add_argument('--plot-type', dest='plot_type', default='power',
                        help='Specify plot type: power, temp, or volt')
    args = parser.parse_args()
    plot_type = args.plot_type
    if args.json_file is None and shutil.which('xbutil') is None:
        print(status_codes['XRT_NOT_SETUP']['message'])
        exit(status_codes['XRT_NOT_SETUP']['code'])

    # add a background task to get xbutil dump every second
    scheduler.add_job(get_xbutil_dump, 'interval', [args.json_file], seconds=1)
    scheduler.start()
    atexit.register(lambda: scheduler.shutdown(wait=True))

    # refresh every 1 second
    animation_power = animation.FuncAnimation(figure_hist, animate_plot, interval=1000)
    main_window.mainloop()


if __name__ == '__main__':
    # start the main GUI
    xbutil_gui_main()



