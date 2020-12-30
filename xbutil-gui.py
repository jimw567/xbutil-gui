import tkinter as tk
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation

# global variables
main_window = tk.Tk()
figure_power = plt.Figure(figsize=(10, 5), dpi=100)
plot_power = figure_power.add_subplot(111)
canvas_power = FigureCanvasTkAgg(figure_power, main_window)
canvas_power.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH)


def animate_power(iter):
    plot_power.clear()
    time_array = [str(i) for i in range(iter)]
    power_array = [6.1 + i for i in range(iter)]
    power_hist_dict = {'Time': time_array,
                       'Power': power_array}
    power_hist_df = DataFrame(power_hist_dict, columns=['Time', 'Power'])
    power_hist_df = power_hist_df[['Time', 'Power']].groupby('Time').sum()
    power_hist_df.plot(kind='line', legend=True, ax=plot_power, color='r', marker='o', fontsize=10)
    plot_power.set_title('Power vs Time')


def xbutil_gui_main():
    # refresh every 1 second
    animation_power = animation.FuncAnimation(figure_power, animate_power, interval=1000)
    main_window.mainloop()


if __name__ == '__main__':
    xbutil_gui_main()

