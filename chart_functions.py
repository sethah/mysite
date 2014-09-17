import data_functions as df
import datetime
import json
import types

def main():
    c = google_chart('column')
    print c.options
    c.options['hAxis']['textStyle']['italic'] = "true"
    print c.options
class google_chart(object):
    def __init__(self, chart_type, chartid):
        self.chart_type = chart_type
        self.data = []
        self.data2 = []
        self.formatters = []
        self.chartid = 'chart-div '+chartid
        self.options = self.init_options()

    def init_options(self):
        #defaults
        width = "70%"
        height = "60%"
        fontSize = 14
        titleFontSize = 16
        legendPosition = 'in'
        default_color = 'blue'
        away_default_color = 'red'

        options = {}
        if self.chart_type == 'column':
            options = {
                "column": "col",
                "chartArea": {"width": width, "height": height},
                "colors": [default_color],
                "hAxis": {"textStyle": {"italic": "false"}, "slantedTextAngle": "45", "fontSize": fontSize, "slantedText": "true", "titleFontSize": fontSize, "title": "Title", "titleTextStyle": {"italic": "false"}},
                "titleFontSize": titleFontSize,
                "vAxis": {"textStyle": {"italic": "false"}, "fontSize": fontSize, "titleTextStyle": {"italic": "false"}, "title": "Title", "titleFontSize": fontSize},
                "legend": {"position": legendPosition}
                }
        elif self.chart_type == 'line':
            options = {
                "focusTarget": "category",
                "chartArea": {"width": width, "height": height},
                "hAxis": {"textStyle": {"italic": "false"}, "fontSize": fontSize, "titleFontSize": fontSize, "title": "Title", "titleTextStyle": {"italic": "false"}, "maxValue": "40", "minValue": "0"},
                "tooltip": {"isHtml": "true"},
                "colors": [default_color, away_default_color],
                "titleFontSize": titleFontSize,
                "vAxis": {"textStyle": {"italic": "false"}, "fontSize": fontSize, "titleFontSize": fontSize, "title": "Title", "titleTextStyle": {"italic": "false"}, "maxValue": "1.8", "minValue": "0"},
                "line": "col",
                "legend": {"position": legendPosition}
                }
        elif self.chart_type == 'pie_diff':
            options = {
                "diff": {"oldData": {"opacity": 0.99}, "innerCircle": {"borderFactor": 0.1}},
                "sliceVisibilityThreshold": 0,
                "titleFontSize": titleFontSize
                }
        return options
    def js_options(self):
        self.options = json.dumps(self.options)

def chart_options(base_options = {},**kwargs):
    options = df.make_dict(
        font = 'Arial',
        hAxis_title='hAxis',
        hAxis_titleFontSize = 14,
        hAxis_fontSize = 14,
        hAxis_slantedText = 'true',
        hAxis_slantedTextAngle = 45,
        vAxis_title='vAxis',
        vAxis_titleFontSize = 14,
        vAxis_fontSize = 14,
        chart_title = '',
        chart_titleFontSize = 16,
        legend_position = 'none',
        chart_areaWidth = '80%',
        chart_areaHeight = '50%',
        column_series = '')
    for key in base_options.keys():
        options[key] = base_options[key]
    for arg in kwargs:
        if arg not in options.keys():
            continue
        options[arg] = kwargs[arg]

    return options
def chart_options2(chart_type,options = None,new_options = None):
    if options == None:
        options = {}
    if new_options == None:
        new_options = {}
    if options == {}:
        #create new options with the appropriate defaults
        vAxis = {}
        hAxis = {}
        chartArea = {}

        if chart_type == 'line':
            options[chart_type] = 'col'
            vAxis['fontSize'] = 14
            vAxis['titleFontSize'] = 14
            vAxis['textStyle'] = {'italic':'false'}
            vAxis['titleTextStyle'] = {'italic':'false'}
            hAxis['fontSize'] = 14
            hAxis['titleFontSize'] = 14
            hAxis['textStyle'] = {'italic':'false'}
            hAxis['titleTextStyle'] = {'italic':'false'}
            options['titleFontSize'] = 16
            options['legend'] = {'position':'in'}
            chartArea['width'] = '70%'
            chartArea['height'] = '60%'
            options['hAxis'] = hAxis
            options['vAxis'] = vAxis
            options['chartArea'] = chartArea
            options['tooltip'] = {'isHtml' : 'true'}
            options['focusTarget']='category'
        elif chart_type == 'column':
            options[chart_type] = 'col'
            vAxis['fontSize'] = 14
            vAxis['titleFontSize'] = 14
            vAxis['textStyle'] = {'italic':'false'}
            vAxis['titleTextStyle'] = {'italic':'false'}
            hAxis['fontSize'] = 14
            hAxis['titleFontSize'] = 14
            hAxis['textStyle'] = {'italic':'false'}
            hAxis['titleTextStyle'] = {'italic':'false'}
            options['titleFontSize'] = 16
            options['legend'] = {'position':'in'}
            chartArea['width'] = '70%'
            chartArea['height'] = '60%'
            options['hAxis'] = hAxis
            options['vAxis'] = vAxis
            options['chartArea'] = chartArea
        elif chart_type == 'pie':
            options['titleFontSize'] = 16
            #options['legend'] = {'position':'labeled'}
            options['sliceVisibilityThreshold'] = 0
            options['diff'] = {}
            options['diff']['oldData'] = { 'opacity': 0.99 }
            options['diff']['innerCircle'] = { 'borderFactor': 0.1}
            chartArea['width'] = '100%'
            chartArea['height'] = '100%'



    #join the old and new options
    options = merge(options,new_options)
    #options = json.dumps(options)
    return options
def merge(x,y):
    # store a copy of x, but overwrite with y's values where applicable
    merged = dict(x,**y)

    xkeys = x.keys()

    # if the value of merged[key] was overwritten with y[key]'s value
    # then we need to put back any missing x[key] values
    for key in xkeys:
        # if this key is a dictionary, recurse
        if type(x[key]) is types.DictType and y.has_key(key):
            merged[key] = merge(x[key],y[key])

    return merged
def game_time_to_datetime(game_time):
    minutes = int(df.myround(game_time,1))
    seconds = int(round((game_time%1)*60))

    return str(minutes).zfill(2)+':'+str(seconds).zfill(2)
if __name__ == "__main__":
    main()

