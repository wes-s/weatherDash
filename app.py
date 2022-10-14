from flask import Flask, request, render_template, make_response
from flask_restful import Api, Resource
from flask import send_file
from flask import send_from_directory
# from pyowm import OWM
from weatherbit.api import Api as wApi
from datetime import datetime, timedelta
import pytz
import pandas as pd
from bokeh.palettes import plasma
from bokeh.plotting import figure, show
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
import math
import os

app = Flask(__name__)
api =  Api(app)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static', 'images'),'favicon.ico', mimetype='image/png')

class getChart(Resource):
    def get(self, locations):
        headers = {'Content-Type': 'text/html'}
        key = 'derp'
        if request.args:
            key = request.args.get('key', 0)
        
        wapi = wApi(key)
        wapi.set_granularity('hourly')

        locations = locations.split(';')
        temps_h = []
        temps_d = []

        def getForecastFromWeatherBit(location, granularity):
            wapi.set_granularity(granularity)
            forecast = wapi.get_forecast(city=location, units='I')
            if granularity == 'hourly':
                att = 'temp'
            else:
                att = 'max_temp'
            t = forecast.get_series([att])
            dict_t = {}
            for num, temp in enumerate(t):
                if granularity == 'hourly' or num > 3:
                    idx = datetime.fromtimestamp(datetime.timestamp(pytz.utc.localize(temp['datetime']))).replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    if num <= 3:
                        idx = datetime.fromtimestamp(
                            datetime.timestamp(
                                pytz.utc.localize(
                                    temp['datetime']))).replace(hour=0, minute=0, second=0, microsecond=0)
                                    #.replace(second=0, microsecond=0, minute=0, hour=temps_h[-1].iloc[-1].name.hour)+timedelta(hours = 2) ##hourly forecasts have been removed from weatherbit free tier
                dict_t.update({idx:
                    {
                        'temp': temp[att]
                    }
                })
            df = pd.DataFrame.from_dict(dict_t, orient='index')
            return df

        for location in locations:
            # temps_h.append(getForecastFromWeatherBit(location,'hourly'))##hourly forecasts have been removed from weatherbit free tier
        #     print(temps_h[-1].iloc[-1].name)
            temps_d.append(getForecastFromWeatherBit(location,'daily')[0:16])

        # tempH = pd.concat(temps_h,axis=1) ##hourly forecasts have been removed from weatherbit free tier
        # tempH.columns = locations ##hourly forecasts have been removed from weatherbit free tier

        tempD = pd.concat(temps_d,axis=1)
        tempD.columns = locations

        colors = plasma(len(locations*2))

        p = figure(width=950, height=600, x_axis_type="datetime")

        for num, location in enumerate(locations, start=0):
            # p.line(tempH.index.values, tempH[0:][location], legend=location, color=colors[num*2+1], line_width=5)##hourly forecasts have been removed from weatherbit free tier
            # p.circle(tempH.index.values, tempH[0:][location],  color=colors[num*2],size=8)##hourly forecasts have been removed from weatherbit free tier
            p.line(tempD.index.values, tempD[0:][location], legend=location, color=colors[num*2+1], line_dash=[10,2], line_width=3)
            p.circle(tempD.index.values, tempD[0:][location],  color=colors[num*2],size=8)
        
        p.xaxis.formatter=DatetimeTickFormatter(
                hours=["%I:00 %p"],
                days=["%A %m-%d"],
                months=["%A %m-%d"],
                years=["%A %m-%d"]
        )
        
        p.xaxis[0].ticker.desired_num_ticks = len(tempD) ## len(tempH) ##hourly forecasts have been removed from weatherbit free tier

        p.xaxis.major_label_orientation = math.pi/4

        p.xaxis.major_label_text_color = '#FFFFFF'
        p.yaxis.major_label_text_color = '#FFFFFF'

        p.xaxis.axis_line_color = '#FFFFFF'
        p.yaxis.axis_line_color = '#FFFFFF'

        p.xaxis.major_tick_line_color = '#FFFFFF'
        p.yaxis.major_tick_line_color = '#FFFFFF'
        p.yaxis.minor_tick_line_color = '#FFFFFF'   

        p.xgrid.grid_line_color = '#333333'
        p.ygrid.grid_line_color = '#333333'

        p.toolbar.logo = None
        p.border_fill_color = '#191919'
        p.background_fill_color = '#191919'
        # p.border_fill_color = '#949494'
        # p.background_fill_color = "#949494"
        p.legend.background_fill_alpha = 0.7
        # output_notebook(hide_banner=True)
        # show(p)
        script, div = components(p)
        return make_response(render_template('index.html', script=script, div=div))

api.add_resource(getChart,"/getChart/<string:locations>")

# run.py in local werkzeug simple server when locally testing
if __name__ == "__main__":
    app.run(debug=True)