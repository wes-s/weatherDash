from flask import Flask, request, render_template, make_response
from flask_restful import Api, Resource, reqparse
import requests
from flask import send_file
from pyowm import OWM
from datetime import datetime, timedelta
import pandas as pd
from bokeh.palettes import Spectral, viridis, magma, plasma
from bokeh.plotting import figure, show, output_notebook
from bokeh.io import export_png
from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.models import DatetimeTickFormatter
import math

app = Flask(__name__)
api = Api(app)

class getChart(Resource):
    def get(self, locations):
        headers = {'Content-Type': 'text/html'}
        key = 'derp'
        if request.args:
            key = request.args.get('key', 0)

        locations = locations.split(';')

        owm = OWM(key)
        def getForecastfromDict(loc):
            obs = owm.weather_at_place(loc)                    # Toponym
            w = obs.get_weather()
            curr_hour = datetime.fromtimestamp(w.get_reference_time())
            dict = {}
            dict.update({curr_hour.replace(second=0, microsecond=0, minute=0, hour=curr_hour.hour)+timedelta(hours=curr_hour.minute//30):
                         {
                             'location': loc
                             ,'timestring':datetime.fromtimestamp(w.get_reference_time()).strftime('%Y-%m-%d %X')
                             ,'status':w.get_status()
                             ,'detstat':w.get_detailed_status()
                             ,'windspeed':w.get_wind()['speed']
        #                      ,'winddirection':w.get_wind()['deg']
                             ,'temp':w.get_temperature('fahrenheit')['temp']
                             ,'temp_max':w.get_temperature('fahrenheit')['temp_max']
                             ,'temp_min':w.get_temperature('fahrenheit')['temp_min']
                             }
                            })
            fc = owm.three_hours_forecast(loc)
            f = fc.get_forecast()
            fw =f.get_weathers()
            for weather in fw:
                timestring = datetime.fromtimestamp(weather.get_reference_time()).strftime('%Y-%m-%d %X')
                dict.update({datetime.fromtimestamp(weather.get_reference_time()):
                             {
                                  'location': loc
                                 ,'timestring': timestring
                                 ,'status':weather.get_status()
                                 ,'detstat':weather.get_detailed_status()
                                 ,'windspeed':weather.get_wind()['speed']
        #                          ,'winddirection':weather.get_wind()['deg']
                                 ,'temp':weather.get_temperature('fahrenheit')['temp']
                                 ,'temp_max':weather.get_temperature('fahrenheit')['temp_max']
                                 ,'temp_min':weather.get_temperature('fahrenheit')['temp_min']
                             }
                            })
            df = pd.DataFrame.from_dict(dict, orient='index')
            return df

        temps = []
        for location in locations:
            temps.append(getForecastfromDict(location)[['temp']])

        temp_c = pd.concat(temps,axis=1)
        temp_c.columns = locations
        colors = viridis(len(locations*2))

        p = figure(width=1000, height=600, x_axis_type="datetime")

        for num, location in enumerate(locations, start=0):
            p.line(temp_c.index.values, temp_c[0:][location], legend=location, color=colors[num*2+1], line_width=4)
            p.circle(temp_c.index.values, temp_c[0:][location],  color=colors[num*2],size=8)
        
        p.xaxis.formatter=DatetimeTickFormatter(
               hours=["%H:00"],
               days=["%m-%d %H:00"],
               months=["%m-%d %H:00"],
               years=["%m-%d %H:00"]
           )
        
        p.xaxis[0].ticker.desired_num_ticks = len(temp_c)*2

        p.xaxis.major_label_orientation = math.pi/4

        p.toolbar.logo = None
        p.toolbar_location = None
        p.border_fill_color = '#949494'
        p.background_fill_color = "#949494"
        # output_notebook(hide_banner=True)
        # show(p)
        script, div = components(p)
        return make_response(render_template('index.html', script=script, div=div))

api.add_resource(getChart,"/getChart/<string:locations>")

# run.py in local werkzeug simple server when locally testing
if __name__ == "__main__":
    app.run(debug=True)