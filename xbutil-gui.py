import tkinter as tk
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
import subprocess
import json
import shutil
import datetime


# global variables
status_codes = {
    'XRT_NOT_SETUP': {
        'code': 1,
        'message': 'ERROR: xbutil not found. Please set up XRT environment before running this application.'
    }
}
main_window = tk.Tk()
figure_power = plt.Figure(figsize=(10, 5), dpi=100)
plot_power = figure_power.add_subplot(111)
canvas_power = FigureCanvasTkAgg(figure_power, main_window)
canvas_power.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)
time_hist = []
power_hist = []
refresh_interval = 10 # seconds between refresh

def get_xbutil_dump():
    command = ['xbutil', 'dump']
    p = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    xbutil_dump = p.stdout.read()
    xbutil_dump_json = json.loads(xbutil_dump.decode('utf-8'))
    #time_hist.append(datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    time_hist.append(datetime.datetime.now().strftime("%H:%M:%S"))
    power_hist.append(int(xbutil_dump_json['board']['physical']['power']))
    #print('temp', json.dumps(xbutil_dump_json['board']['physical']['thermal']['fpga_temp'], indent=4))


def animate_power(iter):
    if iter % refresh_interval > 0:
        return

    get_xbutil_dump()
    plot_power.clear()
    power_hist_dict = {'Time': time_hist[-10:], 'Power': power_hist[-10:]}
    power_hist_df = DataFrame(power_hist_dict, columns=['Time', 'Power'])
    power_hist_df = power_hist_df[['Time', 'Power']].groupby('Time').sum()
    #print(iter, type(power_hist_df['Time']), type(power_hist_df['Power']))
    power_hist_df.plot(kind='line', legend=False, ax=plot_power, color='r', marker='o', fontsize=10)
    plot_power.set_title('Power History')


def xbutil_gui_main():
    # refresh every 1 second
    animation_power = animation.FuncAnimation(figure_power, animate_power, interval=1000)
    main_window.mainloop()


if __name__ == '__main__':
    if shutil.which('xbutil') is None:
        print(status_codes['XRT_NOT_SETUP']['message'])
        exit(status_codes['XRT_NOT_SETUP']['code'])

    xbutil_gui_main()



