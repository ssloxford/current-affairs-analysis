"""
Utilities for the plotting script
"""

import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

sns.set_theme(context="notebook", style="white")
def get_color(id, count):
    def lerp(a, b, x):
        return a * (1-x) + b * x

    x = (id+1) / count
    return ((lerp(1, 0, x)),(lerp(1, (33/255), x)),(lerp(1, (71/255), x)))

new_rc = {
    'xtick.bottom': True,
    'xtick.minor.bottom': True,
    'xtick.minor.visible': True,
    'xtick.top': False,
    'ytick.left': True,
    'ytick.minor.left': True,
    'ytick.minor.visible': True,
    'ytick.right': False,
    'grid.color': "#d0d0d0",
    'grid.linestyle': "--",
    'axes.grid': True,
    'legend.loc': "best",
    'legend.frameon': True,
    #'font.family': "sans-serif",
    'font.family': "serif",
    'font.serif': ["CMU Serif"],
    'font.weight': "bold",
    'font.titleweight': "bold",
    'axes.labelweight': "bold",
    'axes.titleweight': "bold",
    'axes.unicode_minus': False,
    'axes.prop_cycle': plt.cycler(color=['#0077BB', '#EE7733', '#009988', '#BBBBBB', '#EE3377', '#33BBEE', '#CC3311']), #https://personal.sron.nl/~pault/
    #'axes.prop_cycle': plt.cycler(color=[get_color(i, 8) for i in range(8)]),
    'savefig.bbox': "tight",
    'savefig.pad_inches': 0.1,
    #'legend.loc': "lower center",
    #'legend.frameon': False,

}
plt.rcParams |= new_rc

def set_cycler(count, back = False):
    cols = [get_color(i, count) for i in range(count)]
    if back:
        cols = cols[::-1]
    cycler = plt.cycler(color=cols)#type: ignore
    plt.rcParams['axes.prop_cycle'] = cycler
    if plt.gca() is not None:
        plt.gca().set_prop_cycle(cycler)
    return plt.rcParams['axes.prop_cycle'].by_key()['color']

def barplot(columns, rows, data, width = 0.5):

    plt.figure(figsize=(4.5,2.5))
    bottom = np.zeros(len(columns))
    cycler = set_cycler(len(rows))

    for idx, type in enumerate(rows):
        count = data[:,idx]
        plt.bar(columns, count, width, label=type, bottom=bottom, color=cycler[idx])
        bottom += count

    plt.legend(loc="upper left")
    plt.gca().minorticks_off()

    plt.ylim(0, np.max(bottom) * 1.1)

