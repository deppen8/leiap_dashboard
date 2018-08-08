import pandas as pd

#from bokeh.application import Application
#from bokeh.application.handlers import FunctionHandler
from bokeh.io import output_notebook, show, curdoc
# output_notebook()
from bokeh.layouts import widgetbox, row, column, layout
from bokeh.plotting import figure
from bokeh.models.widgets import (MultiSelect,
                                  CheckboxButtonGroup,
                                  TextInput)
from bokeh.models import (ColumnDataSource,
                          Range1d,
                          HoverTool, PanTool, WheelZoomTool, BoxZoomTool, ResetTool,
                          NumeralTickFormatter)


def make_plot(point_source):
    # create empty figure
    p = figure(plot_width=600, plot_height=450, 
               tools=[PanTool(),WheelZoomTool(),BoxZoomTool(),ResetTool()])
    p.xaxis[0].formatter = NumeralTickFormatter(format="0")
    p.yaxis[0].formatter = NumeralTickFormatter(format="0")

    # plot survey points
    p.circle(x='easting', y='northing', source=point_source, line_color='red', radius=5, fill_color=None)
    
    return p


def get_dataset(df):
    # start with the whole dataset
    selected = df.copy()
    # narrow by selected year(s)/date(s) of survey (start date and end date text entry widgets of the form dd-mm-YYYY)
    selected = selected[(selected['DataDate']>=start_date.value)&(selected['DataDate']<=end_date.value)]

    # narrow by selected surveyor(s)
    surveyors_val = surveyors_select.value
    if surveyors_val != ['ALL']:
        selected = selected[selected['SurveyorId'].isin(surveyors_val)]

    # narrow by selected field(s)
    fields_val = fields_select.value
    if fields_val != ['ALL']:
        selected = selected[selected['FieldNumber'].isin(fields_val)]

    # narrow by selected production(s)    
    prods_val = prods_select.value
    if prods_val != ['ALL']:
        for p in prods_val:
            selected = selected[selected[p+'_ct']>0]

    # narrow by artifact count range
    ct_cols = [c for c in selected.columns if c[-3:]=="_ct"]
    selected['sub_count'] = selected[ct_cols].apply('sum', axis=1)
    selected = selected[(selected['sub_count']>=float(count_min.value))&(selected['sub_count']<=float(count_max.value))]

    # narrow by artifact weight range
    wt_cols = [c for c in selected.columns if c[-3:]=="_wt"]
    selected['sub_weight'] = selected[wt_cols].apply('sum', axis=1)
    selected = selected[(selected['sub_weight']>=float(weight_min.value))&(selected['sub_weight']<=float(weight_max.value))]    
    
    return ColumnDataSource(data=dict(easting=selected['Easting'].tolist(), northing=selected['Northing'].tolist()))

def update_plot():
    src = get_dataset(df)
    point_source.data.update(src.data)


df = pd.read_pickle('data.pkl')
    
# date widgets
start_date = TextInput(value=str(df['DataDate'].min().date()), title="Start date (YYYY-MM-DD):")
end_date = TextInput(value=str(df['DataDate'].max().date()), title='End date (YYYY-MM-DD):')

# surveyors
# list of tuples of the form: (id, name)
surveyors = list(df[['SurveyorId','SurveyorName']].sort_values('SurveyorId').apply(lambda x: (str(x[0]),x[1]), axis=1).unique())
surveyors_select = MultiSelect(title="Surveyor(s):", value=['ALL'], options=['ALL']+surveyors, size=7)

# fields
fields = list(df['FieldNumber'].sort_values(axis=0).unique())
fields_select = MultiSelect(title='Field(s)', value=['ALL'], options=['ALL']+fields, size=7)

# productions
prods = [c[:-3] for c in df.columns if c[-3:]=="_ct"]
prods_select = MultiSelect(title='Production(s)', value=['ALL'], options=['ALL']+prods, size=7)

# counts of artifacts per point
ct_cols = [c for c in df.columns if c[-3:]=="_ct"]
df['total_count'] = df[ct_cols].apply('sum', axis=1)

count_min = TextInput(value=str(df['total_count'].min()), title="Min. count per point:")
count_max = TextInput(value=str(df['total_count'].max()), title='Max. count per point:')

# artifact weight
wt_cols = [c for c in df.columns if c[-3:]=="_wt"]
df['total_weight'] = df[wt_cols].apply('sum', axis=1)

weight_min = TextInput(value=str(df['total_weight'].min()), title="Min. weight (g) per point:")
weight_max = TextInput(value=str(df['total_weight'].max()), title='Max. weight (g) per point:')
    
controls = [start_date, end_date,
            surveyors_select,
            fields_select,
            prods_select,
            count_min, count_max,
            weight_min, weight_max]

for control in controls:
    control.on_change('value', lambda attr, old, new: update_plot())

sizing_mode = 'scale_width'  # 'scale_width' also looks nice with this example
# inputs = widgetbox(*controls, sizing_mode=sizing_mode)


point_source = get_dataset(df)
p = make_plot(point_source)

l = layout([[controls],[p]], sizing_mode=sizing_mode)

curdoc().add_root(l)
