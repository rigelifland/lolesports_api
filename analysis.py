import json, requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from bokeh.io import output_notebook, show
from bokeh.plotting import figure
from bokeh.models import HoverTool, ColumnDataSource, NumeralTickFormatter
from bokeh.layouts import Column
output_notebook()

def find_largest_drop(data):
    drop, max_value = 0, 0
    drop_start_idx, drop_end_idx, max_value_idx = 0, 0, 0
    for idx, row in enumerate(data):
        if max_value-row > drop:
            drop = max_value-row
            drop_end_idx = idx
            drop_start_idx = max_value_idx
        if row > max_value:
            max_value = row
            max_value_idx = idx
        max_value = max(max_value, row)
    drop_points = data.iloc[[drop_start_idx, drop_end_idx]]
    return drop, drop_points

def diffPlot(data, title=''):
    s = np.sign(data.iloc[-1])
    drop, drop_points = find_largest_drop(data*s)
    if isinstance(data, pd.Series):
        data = data.to_frame()
    columns = data.columns.values
    data['zero'] = np.zeros(len(data))
    for col in columns:
        data[col + 'Pos'] = data[col].apply(lambda x: max(x, 0))
        data[col + 'Neg'] = data[col].apply(lambda x: min(x, 0))
    source = ColumnDataSource(data)
    p = figure(title=title+ f': largest drop = {drop:,}', plot_width=900, plot_height=400)
    for col in columns:
        p.line('index', col, line_color="black", source=source)
        p.varea('index', y1=col+'Pos', y2='zero', color='#4e79a7', alpha=0.5, source=source)
        p.varea('index', y1=col+'Neg', y2='zero', color='#e15759', alpha=0.5, source=source)
    p.add_tools(HoverTool(
        tooltips=[
            ('time', '@index{00:00:00}'),
            ('value', '@' + col + '{0,0}')
        ],
        mode='vline'
    ))
    p.xaxis.formatter=NumeralTickFormatter(format="00:00:00")
    
    p.x(drop_points.index, drop_points.values*s, size=10, color="black")
    
    #eventFig = figure(plot_width=900, plot_height=30)
    show(p)
    return p