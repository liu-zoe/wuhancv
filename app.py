#%% [markdown]
## Project Name: WUHANCV
### Program Name: app.py
### Purpose: To make a dash board for the bubble plots
##### Date Created: Jan 30th 2020
import os
import pathlib
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import colorlover as cl
import pandas as pd
import numpy as np
import math
import scipy
from scipy.optimize import curve_fit
import datetime
from datetime import datetime as dt
from datetime import date
# Initialize app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "A Time Lapse of the COVID-19 Outbreak"}, 
        {"name": "news_keywords", "content": "COVID-19, Novel Coronavirus, Novel CoronaVirus, Wuhan Coronavirus"}
        ],
    )
server=app.server
#--------------------------Load And Process Data----------------------------#
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
#Load data
csv_names=[
    "time_series_covid19_confirmed_global",
    "time_series_covid19_deaths_global",
    "time_series_covid19_recovered_global",
    "time_series_covid19_confirmed_US",
    "time_series_covid19_deaths_US",
    ]
rawdf=list(map(lambda x: pd.read_csv(os.path.join(APP_PATH, 'data/TimeSeries/'+x+'.csv')),csv_names))
last_column=list(rawdf[0])[-1].split('/')
# Seperate the colonies and islands from Denmark, France, Netherlands & UK
for i in range(3):
    dat=rawdf[i]
    dat=dat.assign(Location=np.where(dat['Province/State'].isnull(),
                        dat['Country/Region'],
                        dat['Country/Region']+'-'+dat['Province/State']))
    dat['Country/Region']=np.where(
        dat['Country/Region'].isin(['Denmark','France','Netherlands','United Kingdom']),
        dat['Location'],
        dat['Country/Region']
    )
    rawdf[i]=dat
del i
# Create a list of dates
init_date=datetime.date(2020,1,22)
#today=date.today()
last_mon=int(last_column[0])
last_day=int(last_column[1])
today=datetime.date(2020,last_mon,last_day)
del last_column, last_mon, last_day
dates_real=[init_date] #list of dates as datetime object
dates=['1/22/20'] #list of dates to extract variables 
dates_short=['Jan22']
cur_date=init_date
while cur_date<today: 
    cur_date=cur_date+datetime.timedelta(days=1)
    dates_real.append(cur_date)
    x=dt.strftime(cur_date,'%m/%e/%y')
    y=dt.strftime(cur_date,'%b%d')
    if x.startswith('0'):
        x=x[1:]
    dates.append(x.replace(' ',''))
    dates_short.append(y)
del cur_date,x,y

# Specify how large the bubble should be
bubble_size_index=7

#Create a subset of all dates to limit the clutter on bubblemap timetrack
skip=5
mark_index=[]
i=len(dates)-1
while (i>=0):
    mark_index.append(i)
    i-=(skip+1)
mark_index.reverse()
del skip, i

# Create the baseline dataset for world bubble map on Jan 22
bubble0=rawdf[0][['Province/State','Country/Region', 'Lat', 'Long', 'Location']]
#bubble0=bubble0.assign(Location=np.where(bubble0['Province/State'].isnull(), bubble0['Country/Region'],\
#    bubble0['Country/Region']+'-'+bubble0['Province/State']))
bubble0=bubble0.assign(Confirmed=rawdf[0]['1/22/20'])
bubble0=bubble0.assign(Deaths=rawdf[1]['1/22/20'])
bubble0=bubble0.assign(Recovered=rawdf[2]['1/22/20'])
bubble0=bubble0.assign(conf=bubble0['Confirmed'].apply(lambda x: (math.log10(x+1))*bubble_size_index if x>0 else 0))
# Create the baseline dataset for US bubble map on Jan 22
bubble_us0=rawdf[4][['Province_State','Country_Region', 'Admin2','Combined_Key','Population','Lat', 'Long_']]
bubble_us0=bubble_us0.assign(Confirmed=rawdf[3]['1/22/20'])
bubble_us0=bubble_us0.assign(Deaths=rawdf[4]['1/22/20'])
bubble_us0=bubble_us0.assign(conf=bubble_us0['Confirmed'].apply(lambda x: (math.log10(x+1))*bubble_size_index if x>0 else 0))

# Write a function to sum up counts by date
def sumbydate(
    indat, #Input Data
):
    tmp=indat[dates]
    sums=tmp.sum()
    return(sums)

# Create Sum of all Countries
all_sums=list(map(lambda x: sumbydate(x), rawdf))
cumu=pd.DataFrame()
cumu['date']=dates_real
cumu['Confirmed']=all_sums[0].values
cumu['Deaths']=all_sums[1].values
cumu['Recovered']=all_sums[2].values
cumu['Days']=np.arange(len(cumu))
cumu['Days']+=1
cumu['death_rate']=round(100*(cumu['Deaths']/cumu['Confirmed']),2)
cumu['recover_rate']=round(100*(cumu['Recovered']/cumu['Confirmed']),2)
cumu_us=pd.DataFrame()
cumu_us['date']=dates_real
cumu_us['Confirmed']=all_sums[3].values
cumu_us['Deaths']=all_sums[4].values
cumu_us['Days']=np.arange(len(cumu_us))
cumu_us['Days']+=1
cumu_us['death_rate']=round(100*(cumu_us['Deaths']/cumu_us['Confirmed']),2)
vars=['Confirmed','Deaths','Recovered', 'death_rate','recover_rate']
yaxislab=['Confirmed Cases', 'Deaths Cases', 'Recovered Cases',
'Death Rates (%)', 'Recovered Rates (%)','New Confirmed Cases',]
charttitle=['Cumulative Confirmed Cases Across Time', 
'Cumulative Deaths Cases Across Time', 
'Cumulative Recovered Cases Across Time', 
'Cumulative Deaths Rates* Across Time', 
'Cumulative Recovered Rates Across Time',
'New Confirmed Cases Across Time',]
#----------------------------------Fit a growth curve-------------------------------#
pred_period=5 #Number of days to plot ahead of today
days_count=len(dates)
max_days=days_count+pred_period
x=np.array(list(cumu['Days']))
y=np.array(list(cumu['Confirmed']))
y_prev=np.array([0,])
y_prev=np.append(y_prev, y[:days_count-1])
y_change=y-y_prev
def sigmoid_func(x, a, k, delta, L):
    y=a+((L-a)/(1+np.exp((k-x)/delta)))
    return y
popt, pcov = curve_fit(sigmoid_func, x, y,maxfev=100000)
xx = np.linspace(1,max_days,max_days)
yy = sigmoid_func(xx, *popt)
d=list()
for i in range(max_days):
    d.append(init_date+datetime.timedelta(days=i))
dd=np.array(d)
del i, d

# Create a color scheme
orcl3=cl.scales['3']['seq']['Oranges']
grcl3=cl.scales['3']['seq']['Greys']
bgcl='#1f2630'
linecl="#BDC6DC"
fontcl="#BDC6DC"
markercl=orcl3[2]

# Fonts
plotly_fonts=["Arial, sans-serif", "Balto, sans-serif", "Courier New, monospace",
            "Droid Sans, sans-serif", "Droid Serif, serif",
            "Droid Sans Mono, sans-serif",
            "Gravitas One, cursive", "Old Standard TT, serif",
            "Open Sans, sans-serif",
            "PT Sans Narrow, sans-serif", "Raleway, sans-serif",
            "Times New Roman, Times, serif"]
plotfont=plotly_fonts[10]
#----------------------------------App Title------------------------------------#
app.title='COVID-19 Outbreak'
#----------------------------------App Layout-----------------------------------#
app.layout = html.Div(
    id="root",
    children=[
            #Header,
            html.Div(
                id="header",
                children=[
                    html.Img(id="logo", src=app.get_asset_url("logo.png")),
                    html.H3(children="COVID-19 Outbreak",
                            style={'textAlign': 'left',},
                    ),
                    dcc.Markdown(
                        id="description",
                        children=
                        '''
                        Data Source: Data used in this project is extracted from 
                        [**Mapping 2019-nCoV**](https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6) 
                        by [Johns Hopkins University Center Center for Systems Science and Engineering](https://systems.jhu.edu/research/public-health/ncov/), 
                        who collected data from various sources, including WHO, U.S. CDC, ECDC China CDC (CCDC), 
                        NHC and DXY.                   
                        '''),
                    ],
                ),        
        dcc.Tabs(
            parent_className='custom-tabs',
            className='custom-tabs-container',
            children=[
            #----------------------------Tab 1: World Map-----------------------------------#
                dcc.Tab(
                    label='Global Outbreak Map', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Left Column
                                html.Div(
                                    className="left-column", 
                                    children=[
                                        html.Div(
                                            className="slider-container", 
                                            id="slider-container",
                                            children=[
                                                html.Button(
                                                    id="play-button",
                                                    children="play",
                                                    n_clicks=0,
                                                    n_clicks_timestamp=-1,
                                                    type='button',
                                                    style = {
                                                        'color':markercl, 
                                                        'textAlign':'center'
                                                    },
                                                ),
                                                html.Button(
                                                    id="pause-button",
                                                    children="Pause",
                                                    n_clicks=0,
                                                    n_clicks_timestamp=-1,
                                                    type='button',
                                                    style = {
                                                        'color':markercl, 
                                                        'textAlign':'center'
                                                    },
                                                ),
                                                dcc.Interval(
                                                    id='auto-stepper',
                                                    interval=1*1000, # in milliseconds
                                                    n_intervals=0,
                                                    max_intervals=0,
                                                    disabled=False,
                                                ),
                                                dcc.Slider(
                                                    id="date-slider",
                                                    min=0, 
                                                    max=len(dates)-1,
                                                    value=0,
                                                    marks={
                                                        str(date_ord):{
                                                            "label":dates_short[date_ord],
                                                            "style": {"transform": "rotate(45deg)"}
                                                        } 
                                                        for date_ord in mark_index
                                                    },
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="bubblemap-container",
                                            id="bubblemap-container",
                                            children=[
                                                html.H5(
                                                    "Confirmed COVID-19 Cases Across The Globe on Jan22",
                                                    className="bubblemap-title",
                                                    id="bubblemap-title",
                                                    style={'textAlign': 'left',},
                                                ),
                                                dcc.Graph(
                                                    className="country-bubble", 
                                                    id="country-bubble",
                                                    figure = go.Figure(
                                                        data=go.Scattergeo(
                                                            lat = bubble0['Lat'],
                                                            lon = bubble0['Long'],
                                                            mode='markers',
                                                            hovertext =bubble0['Location']\
                                                            + '<br> Confirmed:' + bubble0['Confirmed'].astype(str)\
                                                            + '<br> Deaths:' + bubble0['Deaths'].astype(str)\
                                                            + '<br> Recovered:' + bubble0['Recovered'].astype(str),
                                                            marker = go.scattergeo.Marker(
                                                                color = markercl,
                                                                size = bubble0['conf'],
                                                                line=dict(width=0.5),
                                                            ),
                                                            opacity=0.85,
                                                        ),
                                                        layout=dict(                                            
                                                            geo=dict(
                                                                scope="world",
                                                                projection_type="natural earth",
                                                                showland=True,
                                                                landcolor=bgcl,
                                                                showcoastlines=True,
                                                                coastlinecolor=linecl,
                                                                showocean=True,
                                                                oceancolor=bgcl,
                                                                showlakes=False,
                                                                showcountries=True,
                                                                countrycolor = linecl,        
                                                                bgcolor=bgcl,
                                                            ),
                                                            margin=dict(l=0, t=0, b=0, r=0, pad=0),
                                                            paper_bgcolor=bgcl,
                                                            plot_bgcolor=bgcl,
                                                        ),
                                                    ),                                        
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                #Right column
                                html.Div(
                                    className="graph-container",
                                    id="graph-container",
                                    children=[
                                        html.P(
                                            className="chart-selector", 
                                            id="chart-selector",
                                            children="Select Country and Type of Cases:", 
                                            style={'textAlign': 'left',},
                                        ), 
                                        html.Div(
                                            id="drop-downs",
                                            children=[
                                                dcc.Dropdown(
                                                    value="World",
                                                    className="country-dropdown",
                                                    id="country-dropdown1",
                                                    options=[                                                
                                                        {
                                                            "label":"World",
                                                            "value":"World",
                                                        },
                                                        {
                                                            "label":"United States",
                                                            "value":'US',
                                                        },
                                                        {
                                                            "label":"Brazil",
                                                            "value":"Brazil",                                                        
                                                        },
                                                        {
                                                            "label":"India",
                                                            "value":"India",
                                                        },                                                                                                                
                                                        {
                                                            "label":"Russia",
                                                            "value":"Russia",
                                                        },
                                                        {
                                                            "label":"South Africa",
                                                            "value":"South Africa",
                                                        },                                                         
                                                        {
                                                            "label":"Mexico",
                                                            "value":"Mexico",                                                        
                                                        },
                                                        {
                                                            "label":"Peru",
                                                            "value":"Peru",
                                                        },
                                                        {
                                                            "label":"Colombia",
                                                            "value":"Colombia",
                                                        },                                                                                                                                                                        
                                                        {
                                                            "label":"Chile",
                                                            "value":"Chile",   
                                                        },
                                                        {
                                                            "label":"Iran",
                                                            "value":"Iran",
                                                        },
                                                        {
                                                            "label":"Spain",
                                                            "value":"Spain",
                                                        },
                                                        {
                                                            "label":"United Kingdom",
                                                            "value":"United Kingdom",
                                                        },
                                                        {
                                                            "label":"Saudi Arabia",
                                                            "value":"Saudi Arabia",
                                                        },                                                        
                                                        {
                                                            "label":"Pakistan",
                                                            "value":"Pakistan",
                                                        },
                                                        {
                                                            "label":"Argentina",
                                                            "value":"Argentina",                                                        
                                                        }, 
                                                        {
                                                            "label":"Bangladesh",
                                                            "value":"Bangladesh",                                                        
                                                        },
                                                        {
                                                            "label":"Italy",
                                                            "value":"Italy",
                                                        },                                                        
                                                        {
                                                            "label":"Turkey",
                                                            "value":"Turkey",
                                                        },
                                                        {
                                                            "label":"France",
                                                            "value":"France",
                                                        },                                                        
                                                        {
				                                            "label":"Germany",
                                                            "value":"Germany",
                                                        },
                                                        {
                                                            "label":"Iraq",
                                                            "value":"Iraq",                                                        
                                                        },
                                                        {
                                                            "label":"Philippines",
                                                            "value":"Philippines",
                                                        }, 
                                                        {
                                                            "label":"Indonesia",
                                                            "value":"Indonesia",
                                                        },                                                        
                                                        {
                                                            "label":"Canada",
                                                            "value":"Canada",                                                        
                                                        },
                                                        {
                                                            "label":"Qatar",
                                                            "value":"Qatar",
                                                        },
                                                        {
                                                            "label":"Kazakhstan",
                                                            "value":"Kazakhstan",                                                        
                                                        },
                                                        {
                                                            "label":"Ecuador",
                                                            "value":"Ecuador",
                                                        },                                                                                                            
                                                        {
                                                            "label":"Bolivia",
                                                            "value":"Bolivia",                                                        
                                                        },  
                                                        {
                                                            "label":"Egypt",
                                                            "value":"Egypt",                                                        
                                                        },
                                                        {
                                                            "label":"Isreal",
                                                            "value":"Isreal",
                                                        },                                                      
                                                    ],            
                                                ),
                                                dcc.Dropdown(
                                                    value=0,
                                                    id="chart-dropdown",
                                                    className="chart-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Confirmed Cases",
                                                            "value":0,
                                                        },
                                                        {
                                                            "label": "Deaths Cases",
                                                            "value":1,
                                                        },
                                                        {
                                                            "label": "Recovered Cases", 
                                                            "value":2,
                                                        },
                                                        {
                                                            "label": "Deaths Rates",
                                                            "value":3,
                                                        },
                                                        {
                                                            "label": "Recovered Rates",
                                                            "value":4,
                                                        }
                                                    ],                                                    
                                                ),
                                            ],
                                        ),
                                        html.H5("Cumulative Confirmed Cases Across Time",
                                                id="lineplot-title",
                                                style={'textAlign': 'left',},
                                                ),
                                        dcc.Graph(
                                            className="selected-data",
                                            id="selected-data",
                                            figure=go.Figure(
                                                data=go.Scatter(
                                                    x=cumu['date'],
                                                    y=cumu['Confirmed'],
                                                    name='Confirmed',
                                                    mode='lines+markers',
                                                    hovertemplate='%{x}'+'<br>Confirmed Cases:%{y}',
                                                    marker = go.scatter.Marker(
                                                                color = markercl,
                                                    ),
                                                    opacity=0.85,    
                                                ),
                                                layout=dict(
                                                    paper_bgcolor=bgcl,
                                                    plot_bgcolor=bgcl,
                                                    margin=dict(t=0, r=0, b=0, l=0, pad=0,),
                                                    yaxis = dict(zeroline = False,
                                                                title='Confirmed Cases',
                                                                color=linecl, 
                                                                showgrid=False,
                                                                
                                                    ),
                                                    xaxis = dict(zeroline = False,
                                                                title='Date',
                                                                color=linecl,
                                                                showgrid=False,
                                                                tickmode='auto',
                                                                nticks=17,
                                                    ),
                                                    font=dict(
                                                        family=plotfont, size=12, 
                                                        color=fontcl,
                                                    ),
                                                ),
                                            ),
                                        ),
                                        html.P("",
                                                id="lineplot-footnote",
                                                style={'textAlign': 'left',},
                                                ),
                                    ],
                                ),
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H5(
                                    [
                                        "Create by ",
                                        html.A("Zoe Liu", href="http://zoe-liu.com", target="_blank"),
                                    ]
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    **Credit:** style and set-up is mostly based on the Dash sample app 
                                    [*US Opiod Epidemic*](https://dash-gallery.plotly.host/dash-opioid-epidemic/).
                                    '''),
                            ],
                        ),
                    ],
                ),
                #----------------------------Tab 2: US Map-----------------------------------#
                dcc.Tab(
                    label='US Outbreak Map', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app
                        html.Div(
                            className="app-container", 
                            children=[
                                #Left Column
                                html.Div(
                                    className="left-column", 
                                    children=[
                                        html.Div(
                                            className="slider-container", 
                                            children=[
                                                html.Button(
                                                    id="play-button-us",
                                                    children="play",
                                                    n_clicks=0,
                                                    n_clicks_timestamp=-1,
                                                    type='button',
                                                    style = {
                                                        'color':markercl, 
                                                        'textAlign':'center'
                                                    },
                                                ),
                                                html.Button(
                                                    id="pause-button-us",
                                                    children="Pause",
                                                    n_clicks=0,
                                                    n_clicks_timestamp=-1,
                                                    type='button',
                                                    style = {
                                                        'color':markercl, 
                                                        'textAlign':'center'
                                                    },
                                                ),
                                                dcc.Interval(
                                                    id='auto-stepper-us',
                                                    interval=1*1700, # in milliseconds
                                                    n_intervals=0,
                                                    max_intervals=0,
                                                    disabled=False,
                                                ),
                                                dcc.Slider(
                                                    id="date-slider-us",
                                                    min=0, 
                                                    max=len(dates)-1,
                                                    value=0,
                                                    marks={
                                                        str(date_ord):{
                                                            "label":dates_short[date_ord],
                                                            "style": {"transform": "rotate(45deg)"}
                                                        } 
                                                        for date_ord in mark_index
                                                    },
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="bubblemap-container",
                                            children=[
                                                html.H5(
                                                    "Confirmed COVID-19 Cases in the US on Jan22",
                                                    className="bubblemap-title",
                                                    id="bubblemap-title-us",
                                                    style={'textAlign': 'left',},
                                                ),
                                                dcc.Graph(
                                                    className="country-bubble", 
                                                    id="country-bubble-us",
                                                    figure = go.Figure(
                                                        data=go.Scattergeo(
                                                            lat = bubble_us0['Lat'],
                                                            lon = bubble_us0['Long_'],
                                                            mode='markers',
                                                            hovertext =bubble_us0['Combined_Key']\
                                                            + '<br> Confirmed:' + bubble_us0['Confirmed'].astype(str)\
                                                            + '<br> Deaths:' + bubble_us0['Deaths'].astype(str),
                                                            marker = go.scattergeo.Marker(
                                                                color = markercl,
                                                                size = bubble_us0['conf'],
                                                                line=dict(width=0.5),
                                                            ),
                                                            opacity=0.85,
                                                        ),
                                                        layout=dict(                                            
                                                            geo=dict(
                                                                scope="usa",
                                                                showland=True,
                                                                landcolor=bgcl,
                                                                showcoastlines=True,
                                                                coastlinecolor=linecl,
                                                                showocean=True,
                                                                oceancolor=bgcl,
                                                                showlakes=False,
                                                                showcountries=True,
                                                                countrycolor = linecl,        
                                                                bgcolor=bgcl,
                                                            ),
                                                            margin=dict(l=0, t=0, b=0, r=0, pad=0),
                                                            paper_bgcolor=bgcl,
                                                            plot_bgcolor=bgcl,
                                                        ),
                                                    ),                                        
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                #Right column
                                html.Div(
                                    className="graph-container",
                                    children=[
                                        html.P(
                                            className="chart-selector", 
                                            children="Select State and Type of Cases:", 
                                            style={'textAlign': 'left',},
                                        ), 
                                        html.Div(
                                            id="drop-downs-us",
                                            children=[
                                                dcc.Dropdown(
                                                    value="US",
                                                    className="country-dropdown",
                                                    id="country-dropdown-us",
                                                    options=[                                                
                                                        {
                                                            "label":"USA",
                                                            "value":"US",
                                                        },
                                                        {
                                                            "label":"Alabama",
                                                            "value":"Alabama",
                                                        },
                                                        {
                                                            "label":"Alaska",
                                                            "value":"Alaska",
                                                        },
                                                        {
                                                            "label":"Arizona",
                                                            "value":"Arizona",
                                                        },
                                                        {
                                                            "label":"Arkansas",
                                                            "value":"Arkansas",
                                                        },
                                                        {
                                                            "label":"California",
                                                            "value":"California",
                                                        },
                                                        {
                                                            "label":"Colorado",
                                                            "value":"Colorado",
                                                        },
                                                        {
                                                            "label":"Connecticut",
                                                            "value":"Connecticut",
                                                        },
                                                        {
                                                            "label":"Delaware",
                                                            "value":"Delaware",
                                                        },
                                                        {
                                                            "label":"DC",
                                                            "value":"District of Columbia",
                                                        },
                                                        {
                                                            "label":"Florida",
                                                            "value":"Florida",
                                                        },
                                                        {
                                                            "label":"Georgia",
                                                            "value":"Georgia",                                                        
                                                        },
                                                        {
                                                            "label":"Hawaii",
                                                            "value":"Hawaii",                                                        
                                                        },
                                                        {
                                                            "label":"Idaho",
                                                            "value":"Idaho",                                                        
                                                        },
                                                        {
                                                            "label":"Illinois",
                                                            "value":"Illinois",                                                        
                                                        },
                                                        {
                                                            "label":"Indiana",
                                                            "value":"Indiana",                                                        
                                                        },
                                                        {
                                                            "label":"Iowa",
                                                            "value":"Iowa",
                                                        },
                                                        {
                                                            "label":"Kansas",
                                                            "value":"Kansas",
                                                        },
                                                        {
                                                            "label":"Kentucky",
                                                            "value":"Kentucky",
                                                        },
                                                        {
                                                            "label":"Louisiana",
                                                            "value":"Louisiana",
                                                        },
                                                        {
                                                            "label":"Maine",
                                                            "value":"Maine",
                                                        },
                                                        {
                                                            "label":"Maryland",
                                                            "value":"Maryland",
                                                        },
                                                        {
                                                            "label":"Massachusetts",
                                                            "value":"Massachusetts",
                                                        },
                                                        {
                                                            "label":"Michigan",
                                                            "value":"Michigan",
                                                        },
                                                        {
                                                            "label":"Minnesota",
                                                            "value":"Minnesota",
                                                        },
                                                        {
                                                            "label":"Mississippi",
                                                            "value":"Mississippi",
                                                        },
                                                        {
                                                            "label":"Missouri",
                                                            "value":"Missouri",
                                                        },
                                                        {
                                                            "label":"Montana",
                                                            "value":"Montana",
                                                        },
                                                        {
                                                            "label":"Nebraska",
                                                            "value":"Nebraska",
                                                        },
                                                        {
                                                            "label":"Nevada",
                                                            "value":"Nevada",
                                                        },
                                                        {
                                                            "label":"New Hampshire",
                                                            "value":"New Hampshire",
                                                        },
                                                        {
                                                            "label":"New Jersey",
                                                            "value":"New Jersey",
                                                        },
                                                        {
                                                            "label":"New Mexico",
                                                            "value":"New Mexico",
                                                        },
                                                        {
                                                            "label":"New York",
                                                            "value":"New York",
                                                        },
                                                        {
                                                            "label":"North Carolina",
                                                            "value":"North Carolina",
                                                        },
                                                        {
                                                            "label":"North Dakota",
                                                            "value":"North Dakota",
                                                        },
                                                        {
                                                            "label":"Ohio",
                                                            "value":"Ohio",
                                                        },
                                                        {
                                                            "label":"Oklahoma",
                                                            "value":"Oklahoma",
                                                        },
                                                        {
                                                            "label":"Oregon",
                                                            "value":"Oregon",
                                                        },
                                                        {
                                                            "label":"Pennsylvania",
                                                            "value":"Pennsylvania",
                                                        },
                                                        {
                                                            "label":"Rhode Island",
                                                            "value":"Rhode Island",
                                                        },
                                                        {
                                                            "label":"South Carolina",
                                                            "value":"South Carolina",
                                                        },
                                                        {
                                                            "label":"South Dakota",
                                                            "value":"South Dakota",
                                                        },
                                                        {
                                                            "label":"Tennessee",
                                                            "value":"Tennessee",
                                                        },
                                                        {
                                                            "label":"Texas",
                                                            "value":"Texas",
                                                        },
                                                        {
                                                            "label":"Utah",
                                                            "value":"Utah",
                                                        },
                                                        {
                                                            "label":"Vermont",
                                                            "value":"Vermont",
                                                        },
                                                        {
                                                            "label":"Virginia",
                                                            "value":"Virginia",
                                                        },
                                                        {
                                                            "label":"Washington",
                                                            "value":"Washington",
                                                        },
                                                        {
                                                            "label":"West Virginia",
                                                            "value":"West Virginia",
                                                        },
                                                        {
                                                            "label":"Wisconsin",
                                                            "value":"Wisconsin",
                                                        },
                                                        {
                                                            "label":"Wyoming",
                                                            "value":"Wyoming",
                                                        },
                                                    ],            
                                                ),
                                                dcc.Dropdown(
                                                    value=0,
                                                    id="chart-dropdown-us",
                                                    className="chart-dropdown",
                                                    options=[
                                                        {
                                                            "label": "Confirmed Cases",
                                                            "value":0,
                                                        },                                                        
                                                        {
                                                            "label": "New Confirmed Cases",
                                                            "value":5,
                                                        },
                                                        {
                                                            "label": "Deaths Cases",
                                                            "value":1,
                                                        },
                                                        {
                                                            "label": "Deaths Rates",
                                                            "value":3,
                                                        },
                                                    ],                                                    
                                                ),
                                            ],
                                        ),
                                        html.H5("Cumulative Confirmed Cases Across Time",
                                                id="lineplot-title-us",
                                                style={'textAlign': 'left',},
                                                ),
                                        dcc.Graph(
                                            className="selected-data",
                                            id="selected-data-us",
                                            figure=go.Figure(
                                                data=go.Scatter(
                                                    x=cumu_us['date'],
                                                    y=cumu_us['Confirmed'],
                                                    name='Confirmed',
                                                    mode='lines+markers',
                                                    hovertemplate='%{x}'+'<br>Confirmed Cases:%{y}',                                          
                                                    marker = go.scatter.Marker(
                                                                color = markercl,
                                                    ),
                                                    opacity=0.85,    
                                                ),
                                                layout=dict(
                                                    paper_bgcolor=bgcl,
                                                    plot_bgcolor=bgcl,
                                                    margin=dict(t=0, r=0, b=0, l=0, pad=0,),
                                                    yaxis = dict(zeroline = False,
                                                                title='Confirmed Cases',
                                                                color=linecl, 
                                                                showgrid=False,
                                                                
                                                    ),
                                                    xaxis = dict(zeroline = False,
                                                                title='Date',
                                                                color=linecl,
                                                                showgrid=False,
                                                                tickmode='auto',
                                                                nticks=17,
                                                    ),
                                                    font=dict(
                                                        family=plotfont, size=12, 
                                                        color=fontcl,
                                                    ),
                                                ),
                                            ),
                                        ),
                                        html.P("",
                                                id="lineplot-footnote-us",
                                                style={'textAlign': 'left',},
                                                ),
                                    ],
                                ),
                            ],
                        ),
                        #Footer
                        html.Div(
                            className="footer",
                            children=[
                                html.H5(
                                    [
                                        "Create by ",
                                        html.A("Zoe Liu", href="http://zoe-liu.com", target="_blank"),
                                    ]
                                ),
                                dcc.Markdown(
                                    className="credit",
                                    children=
                                    '''
                                    **Credit:** style and set-up is mostly based on the Dash sample app 
                                    [*US Opiod Epidemic*](https://dash-gallery.plotly.host/dash-opioid-epidemic/).
                                    '''),
                            ],
                        ),
                    ],
                ),
                #----------------------------Tab 3: Growth Curve-----------------------------#
                dcc.Tab(
                    label='Growth Curve', 
                    className='custom-tab',
                    selected_className='custom-tab--selected',
                    children=[
                        #app - Growth Curve
                        html.Div(
                            className="app-container",
                            children=[
                                #Left Column
                                html.Div(
                                    className="left-column",
                                    children=[
                                        html.Div(
                                            id="drop-downs2",
                                            children=[
                                                dcc.Dropdown(
                                                    className="country-dropdown",
                                                    id="country-dropdown2",
                                                    value="World",
                                                    options=[
                                                        {
                                                            "label":"World",
                                                            "value":"World",
                                                        },
                                                        {
                                                            "label":"United States",
                                                            "value":'US',
                                                        },
                                                        {
                                                            "label":"Brazil",
                                                            "value":"Brazil",                                                        
                                                        },
                                                        {
                                                            "label":"India",
                                                            "value":"India",
                                                        },                                                                                                                
                                                        {
                                                            "label":"Russia",
                                                            "value":"Russia",
                                                        },
                                                        {
                                                            "label":"South Africa",
                                                            "value":"South Africa",
                                                        },                                                         
                                                        {
                                                            "label":"Mexico",
                                                            "value":"Mexico",                                                        
                                                        },
                                                        {
                                                            "label":"Peru",
                                                            "value":"Peru",
                                                        },
                                                        {
                                                            "label":"Colombia",
                                                            "value":"Colombia",
                                                        },                                                                                                                                                                        
                                                        {
                                                            "label":"Chile",
                                                            "value":"Chile",   
                                                        },
                                                        {
                                                            "label":"Iran",
                                                            "value":"Iran",
                                                        },
                                                        {
                                                            "label":"Spain",
                                                            "value":"Spain",
                                                        },
                                                        {
                                                            "label":"United Kingdom",
                                                            "value":"United Kingdom",
                                                        },
                                                        {
                                                            "label":"Saudi Arabia",
                                                            "value":"Saudi Arabia",
                                                        },                                                        
                                                        {
                                                            "label":"Pakistan",
                                                            "value":"Pakistan",
                                                        },
                                                        {
                                                            "label":"Argentina",
                                                            "value":"Argentina",                                                        
                                                        }, 
                                                        {
                                                            "label":"Bangladesh",
                                                            "value":"Bangladesh",                                                        
                                                        },
                                                        {
                                                            "label":"Italy",
                                                            "value":"Italy",
                                                        },                                                        
                                                        {
                                                            "label":"Turkey",
                                                            "value":"Turkey",
                                                        },
                                                        {
                                                            "label":"France",
                                                            "value":"France",
                                                        },                                                        
                                                        {
				                                            "label":"Germany",
                                                            "value":"Germany",
                                                        },
                                                        {
                                                            "label":"Iraq",
                                                            "value":"Iraq",                                                        
                                                        },
                                                        {
                                                            "label":"Philippines",
                                                            "value":"Philippines",
                                                        }, 
                                                        {
                                                            "label":"Indonesia",
                                                            "value":"Indonesia",
                                                        },                                                        
                                                        {
                                                            "label":"Canada",
                                                            "value":"Canada",                                                        
                                                        },
                                                        {
                                                            "label":"Qatar",
                                                            "value":"Qatar",
                                                        },
                                                        {
                                                            "label":"Kazakhstan",
                                                            "value":"Kazakhstan",                                                        
                                                        },
                                                        {
                                                            "label":"Ecuador",
                                                            "value":"Ecuador",
                                                        },                                                                                                            
                                                        {
                                                            "label":"Bolivia",
                                                            "value":"Bolivia",                                                        
                                                        },  
                                                        {
                                                            "label":"Egypt",
                                                            "value":"Egypt",                                                        
                                                        },
                                                        {
                                                            "label":"Isreal",
                                                            "value":"Isreal",
                                                        }, 
                                                    ],
                                                ),
                                                dcc.Input(
                                                    id="days",
                                                    placeholder='Days to project',
                                                    type='text',
                                                    value=''
                                                ),  
                                            ],
                                        ),
                                        html.H5("Cumulative Confirmed Cases with Fitted Curve in the World",
                                            id="curve-title",
                                            style={'textAlign':'left',},
                                        ),
                                        dcc.Graph(
                                            id="curve-plot",
                                            figure=go.Figure(
                                                data=[
                                                    go.Scatter(
                                                        x=dd,
                                                        y=y,
                                                        mode='markers',
                                                        name="Data",
                                                        hovertemplate='Date: %{x}'+'<br>'+'Confirmed:'+'%{y}',
                                                        marker=go.scatter.Marker(
                                                            color=orcl3[2]
                                                        ),
                                                        opacity=0.85,
                                                    ),
                                                    go.Scatter(
                                                        x=dd,
                                                        y=yy,
                                                        mode='lines',
                                                        name="Fit",
                                                        hovertemplate='Date: %{x}'+'<br>'+'Fit:'+'%{y}',
                                                        marker=go.scatter.Marker(
                                                            color='rgb(31, 119, 180)'
                                                        ),
                                                        opacity=0.85,   
                                                    ),
                                                ],
                                                layout=dict(
                                                    paper_bgcolor=bgcl,
                                                    plot_bgcolor=bgcl,
                                                    margin=dict(l=0, t=0, b=0, r=0, pad=0),
                                                    xaxis=dict(
                                                        zeroline=False,
                                                        title='Date',
                                                        showgrid=False,
                                                        color=linecl,
                                                        ),
                                                    yaxis=dict(
                                                        zeroline=False,
                                                        title='Cumulative Confirmed Cases',
                                                        showgrid=False,
                                                        color=linecl,
                                                        ),
                                                    font=dict(
                                                        family=plotfont, size=12, 
                                                        color=fontcl,
                                                    ),
                                                    legend = dict(
                                                        x=0.01, y=1
                                                    )
                                                ),
                                            ),
                                        ),
                                        html.P(
                                            children="Data are fitted with Sigmoid functions.",
                                            id="curve-plot-footnote",
                                            style={'textAlign': 'left',},
                                        ),
                                    ],
                                ),
                                #Right column
                                html.Div(
                                    className="right-column",
                                    children=[
                                        html.P("        "),
                                        html.P("        "),
                                        html.H5(
                                            id="daily-title",
                                            children="Daily New Confirmed Cases in the World",
                                            style={'textAlign': 'left',},
                                        ),
                                        dcc.Graph(
                                            id="bar-plot",
                                            figure=go.Figure(
                                                data=go.Bar(
                                                        x=dd[:days_count],
                                                        y=y_change,
                                                        name="New Cases",
                                                        hovertemplate='%{y} on %{x}',
                                                        marker=dict(
                                                            color=markercl,
                                                            line=dict(
                                                                width=0,
                                                            )
                                                        ),
                                                        opacity=0.85,
                                                ),
                                                layout=dict(
                                                        paper_bgcolor=bgcl,
                                                        plot_bgcolor=bgcl,
                                                        margin=dict(l=0, t=0, b=0, r=0, pad=0),
                                                        font=dict(
                                                            family=plotfont, 
                                                            size=12, 
                                                            color=fontcl,
                                                        ),
                                                        xaxis=dict(
                                                            zeroline=False,
                                                            title='Date',
                                                            showgrid=False,
                                                            color=linecl,
                                                            ),
                                                        yaxis=dict(
                                                            zeroline=False,
                                                            title='New Confirmed Cases',
                                                            showgrid=False,
                                                            color=linecl,
                                                            ),
                                                ),
                                            ),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    ],
                ), 
            ],
        ),       
    ],
)
#-----------------------------------------------------------------------------#
#                                  Callback
# ----------------------------------------------------------------------------#

#--------------------------Global Bubble Map----------------------------------#
#~~~~~~~~~~~~Bubble Plot Slider~~~~~~~~~~~#
@app.callback(
    [
        Output("country-bubble", "figure"), 
        Output("bubblemap-title", "children"),
    ],
    [Input("date-slider", "value")],
)

def update_bubble(date_index):
    datevar=dates[date_index]
    bubble=pd.DataFrame()
    bubble=rawdf[0][['Province/State','Country/Region', 'Lat', 'Long', 'Location']]
    #bubble=bubble.assign(Location=np.where(bubble['Province/State'].isnull(), bubble['Country/Region'],\
    #    bubble['Country/Region']+'-'+bubble['Province/State']))
    bubble=bubble.assign(Confirmed=rawdf[0][datevar])
    bubble=bubble.assign(Deaths=rawdf[1][datevar])
    bubble=bubble.assign(Recovered=rawdf[2][datevar])
    bubble=bubble.assign(conf=bubble['Confirmed'].apply(lambda x: (math.log10(x+1))*bubble_size_index if x>0 else 0))

    fig = go.Figure(
        data=go.Scattergeo(
            lat = bubble['Lat'],
            lon = bubble['Long'],
            mode='markers',
            hovertext =bubble['Location']+ '<br> Confirmed:' + bubble['Confirmed'].astype(str)\
                                              + '<br> Deaths:' + bubble['Deaths'].astype(str)\
                                              + '<br> Recovered:' + bubble['Recovered'].astype(str),
            marker = go.scattergeo.Marker(
                    color = markercl,
                    size = bubble['conf'],
                    line=dict(width=0.5),
                ),
                opacity=0.85,
        )   
    )
    fig.update_layout(
        geo=dict(
            scope="world",
            projection_type="natural earth",
            showcoastlines=True,
            coastlinecolor=linecl,
            showland=True,
            landcolor=bgcl,
            showlakes=False,
            showocean=True,
            oceancolor=bgcl,
            showcountries=True,
            countrycolor = linecl,        
            bgcolor=bgcl,
        ),
        margin=dict(l=0, t=0, b=0, r=0, pad=0),
        paper_bgcolor=bgcl,
        plot_bgcolor=bgcl,
    )
    return fig, "Confirmed COVID-19 Cases Across The Globe on "+dates_short[date_index]

#~~~~~~~~~~~~~~~~~Interval of the Bubble Map~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output('date-slider', 'value'),
        Output('auto-stepper', 'max_intervals'),
        Output('auto-stepper', 'disabled'),
    ],
    [
        Input('auto-stepper', 'n_intervals'),
        Input('play-button','n_clicks_timestamp'),
        Input('pause-button','n_clicks_timestamp')
    ]
)
def move_frames(n_intervals, play_timestamp, pause_timestamp):
    slider_value=0
    max_intervals=0
    int_disabled=True
    if (play_timestamp==-1) & (pause_timestamp==-1):
        return 0, 0, True
    elif  (play_timestamp>pause_timestamp):
        slider_value=(n_intervals+1)%(len(dates))
        max_intervals=-1
        int_disabled=False
    elif (pause_timestamp>play_timestamp):
        slider_value=(n_intervals+1)%(len(dates))
        max_intervals=0
        int_disabled=False
    return slider_value, max_intervals, int_disabled

#~~~~~~~~~~~~~~~~~~~~~Line Plot~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output("lineplot-title", "children"), 
        Output("lineplot-footnote","children")
    ],
    [
        Input("chart-dropdown", "value"),
    ],
)
def update_chart_title(chart_dropdown):
    if chart_dropdown==3:
        footnote="*Death rates are estimated by dividing number of death cases\
            by the number of confirmed cases. Due to the delay of testing or reporting\
                infection cases, actual death rate would be lower."
    else:
        footnote=""
    return charttitle[chart_dropdown],footnote

@app.callback(
    Output("selected-data", "figure"),
    [
        Input("chart-dropdown","value"),
        Input("country-dropdown1","value"),
    ],
)
def display_selected_data(chart_dropdown, country_dropdown):
    if country_dropdown=="World":
        cumux=cumu
    else:
        df0=[]
        for dataframe in rawdf[:3]:
            df0.append(dataframe[dataframe['Country/Region']==country_dropdown])
        sums=list(map(lambda x: sumbydate(x), df0))

        cumux=pd.DataFrame()
        cumux['date']=dates_real
        cumux['Confirmed']=sums[0].values
        cumux['Deaths']=sums[1].values
        cumux['Recovered']=sums[2].values
        cumux['Days']=np.arange(len(cumux))
        cumux['Days']+=1
        cumux['death_rate']=round(100*(cumux['Deaths']/cumux['Confirmed']),2)
        cumux['recover_rate']=round(100*(cumux['Recovered']/cumux['Confirmed']),2)
    yvar=vars[chart_dropdown]
    cumu_one_var=cumux[cumux[yvar]>0][['date', yvar]]
    fig=go.Figure(
        data=go.Scatter(
            x=cumu_one_var['date'],
            y=cumu_one_var[yvar],
            name='',
            mode='lines+markers',
            hovertemplate='%{x}'+'<br>'+yaxislab[chart_dropdown]+':%{y}',
            marker = go.scatter.Marker(
                        color = markercl,
            ),
            opacity=0.85,     
        ),
    )
    fig.update_layout(
        paper_bgcolor=bgcl, 
        plot_bgcolor=bgcl,
        margin=dict(l=0, t=0, b=0, r=0, pad=0),
        yaxis = dict(zeroline = False,
                    title=yaxislab[chart_dropdown],
                    color=linecl, 
                    showgrid=False,
        ),
        xaxis = dict(zeroline = False,
                    title='Date',
                    color=linecl,
                    showgrid=False,
                    tickmode='auto',
                    nticks=17,
                    tickangle=45,
        ),
        font=dict(
            family=plotfont, 
            size=11, 
            color=fontcl,
        ),
    )
    return fig 
#------------------------------US Bubble Map----------------------------------#
#~~~~~~~~~~~~Bubble Plot Slider~~~~~~~~~~~#
@app.callback(
    [
        Output("country-bubble-us", "figure"), 
        Output("bubblemap-title-us", "children"),
    ],
    [Input("date-slider-us", "value")],
)

def update_bubble_us(date_index):
    datevar=dates[date_index]
    bubble_us=pd.DataFrame()
    bubble_us=rawdf[4][['Province_State', 'Country_Region', 'Lat', 'Long_', 'Combined_Key']]
    bubble_us=bubble_us.assign(Confirmed=rawdf[3][datevar])
    bubble_us=bubble_us.assign(Deaths=rawdf[4][datevar])
    bubble_us=bubble_us.assign(conf=bubble_us['Confirmed'].apply(lambda x: (math.log10(x+1))*bubble_size_index if x>0 else 0))
    fig = go.Figure(
        data=go.Scattergeo(
            lat = bubble_us['Lat'],
            lon = bubble_us['Long_'],
            mode='markers',
            hovertext =bubble_us['Combined_Key']+'<br> Confirmed:'+bubble_us['Confirmed'].astype(str)\
                                              + '<br> Deaths:'+bubble_us['Deaths'].astype(str),
            marker = go.scattergeo.Marker(
                    color = markercl,
                    size = bubble_us['conf'],
                    line=dict(width=0.5),
                ),
                opacity=0.85,
        )   
    )
    fig.update_layout(
        geo=dict(
            scope="usa",
            showcoastlines=True,
            coastlinecolor=linecl,
            showland=True,
            landcolor=bgcl,
            showlakes=False,
            showocean=True,
            oceancolor=bgcl,
            showcountries=True,
            countrycolor = linecl,        
            bgcolor=bgcl,
        ),
        margin=dict(l=0, t=0, b=0, r=0, pad=0),
        paper_bgcolor=bgcl,
        plot_bgcolor=bgcl,
    )
    return fig, "Confirmed COVID-19 Cases in the US on "+dates_short[date_index]

#~~~~~~~~~~~~~~~~~Interval of the Bubble Map~~~~~~~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output('date-slider-us', 'value'),
        Output('auto-stepper-us', 'max_intervals'),
        Output('auto-stepper-us', 'disabled'),
    ],
    [
        Input('auto-stepper-us', 'n_intervals'),
        Input('play-button-us','n_clicks_timestamp'),
        Input('pause-button-us','n_clicks_timestamp')
    ]
)
def move_frames_us(n_intervals, play_timestamp, pause_timestamp):
    slider_value=0
    max_intervals=0
    int_disabled=True
    if (play_timestamp==-1) & (pause_timestamp==-1):
        return 0, 0, True
    elif  (play_timestamp>pause_timestamp):
        slider_value=(n_intervals+1)%(len(dates))
        max_intervals=-1
        int_disabled=False
    elif (pause_timestamp>play_timestamp):
        slider_value=(n_intervals+1)%(len(dates))
        max_intervals=0
        int_disabled=False
    return slider_value, max_intervals, int_disabled

#~~~~~~~~~~~~~~~~~~~~~Line Plot~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output("lineplot-title-us", "children"), 
        Output("lineplot-footnote-us","children")
    ],
    [
        Input("chart-dropdown-us", "value"),
    ],
)
def update_chart_title_us(chart_dropdown):
    if chart_dropdown==3:
        footnote="*Death rates are estimated by dividing number of death cases\
            by the number of confirmed cases. Due to the delay of testing or reporting\
                infection cases, actual death rate would be lower."
    else:
        footnote=""
    return charttitle[chart_dropdown],footnote

@app.callback(
    Output("selected-data-us", "figure"),
    [
        Input("chart-dropdown-us","value"),
        Input("country-dropdown-us","value"),
    ],
)
def display_selected_data_us(chart_dropdown, state_dropdown):
    if chart_dropdown<5:
        if state_dropdown=="US":
            cumux_us=cumu_us
        else:
            df0=[]
            for dataframe in rawdf[3:]:
                df0.append(dataframe[dataframe['Province_State']==state_dropdown])
            sums=list(map(lambda x: sumbydate(x), df0))
            cumux_us=pd.DataFrame()
            cumux_us['date']=dates_real
            cumux_us['Confirmed']=sums[0].values
            cumux_us['Deaths']=sums[1].values
            cumux_us['Days']=np.arange(len(cumux_us))
            cumux_us['Days']+=1
            cumux_us['death_rate']=round(100*(cumux_us['Deaths']/cumux_us['Confirmed']),2)
        yvar=vars[chart_dropdown]
        cumu_one_var=cumux_us[cumux_us[yvar]>0][['date', yvar]]
        fig=go.Figure(
            data=go.Scatter(
                x=cumu_one_var['date'],
                y=cumu_one_var[yvar],
                name='',
                mode='lines+markers',
                hovertemplate='%{x}'+'<br>'+yaxislab[chart_dropdown]+':%{y}',
                marker = go.scatter.Marker(
                            color = markercl,
                ),
                opacity=0.85,     
            ),
        )
        fig.update_layout(
            paper_bgcolor=bgcl, 
            plot_bgcolor=bgcl,
            margin=dict(l=0, t=0, b=0, r=0, pad=0),
            yaxis = dict(zeroline = False,
                        title=yaxislab[chart_dropdown],
                        color=linecl, 
                        showgrid=False,
            ),
            xaxis = dict(zeroline = False,
                        title='Date',
                        color=linecl,
                        showgrid=False,
                        tickmode='auto',
                        nticks=17,
                        tickangle=45,
            ),
            font=dict(
                family=plotfont, 
                size=11, 
                color=fontcl,
            ),
        )
    else: #New Daily Cases
        if state_dropdown=="US":
            cumux_us=cumu_us
        else:
            df0=[]
            for dataframe in rawdf[3:]:
                df0.append(dataframe[dataframe['Province_State']==state_dropdown])
            sums=list(map(lambda x: sumbydate(x), df0))
            cumux_us=pd.DataFrame()
            cumux_us['date']=dates_real
            cumux_us['Confirmed']=sums[0].values
            cumux_us['Deaths']=sums[1].values
            cumux_us['Days']=np.arange(len(cumux_us))
            cumux_us['Days']+=1
            cumux_us['death_rate']=round(100*(cumux_us['Deaths']/cumux_us['Confirmed']),2)
        days_count=len(dates)
        #x=np.array(list(cumux_us['Days']))
        y=np.array(list(cumux_us['Confirmed']))
        y_prev=np.append(np.array([0,]), y[:days_count-1])
        y_change=y-y_prev

        fig=go.Figure(
            data=go.Bar(
                x=dates_real,
                y=y_change,
                name='New Caess',
                hovertemplate='%{y} on %{x}',
                marker = dict(
                    color = markercl,
                    line=dict(
                        width=0,
                    )
                ),
                opacity=0.85,     
            ),
        )
        fig.update_layout(
            paper_bgcolor=bgcl, 
            plot_bgcolor=bgcl,
            margin=dict(l=0, t=0, b=0, r=0, pad=0),
            yaxis = dict(zeroline = False,
                        title=yaxislab[chart_dropdown],
                        color=linecl, 
                        showgrid=False,
            ),
            xaxis = dict(zeroline = False,
                        title='Date',
                        color=linecl,
                        showgrid=False,
                        tickmode='auto',
                        nticks=17,
                        tickangle=45,
            ),
            font=dict(
                family=plotfont, 
                size=11, 
                color=fontcl,
            ),
        )
    return fig 
#~~~~~~~~~~~~~~~~~~~~~Growth Curve Titles~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    [
        Output("curve-title", "children"),
        Output("daily-title", "children"), 
    ],
    [
        Input("country-dropdown2", "value"),
    ],
)
def update_curve_title(country_dropdown):
    if country_dropdown=="World":
        curve_title="Cumulative Confirmed Cases with Fitted Curve in the %s" %(country_dropdown)
        daily_title="Daily New Confirmed Cases in the %s" %(country_dropdown)

    else:
        curve_title="Cumulative Confirmed Cases with Fitted Curve in %s" %(country_dropdown)
        daily_title="Daily New Confirmed Cases in %s" %(country_dropdown)
    return curve_title, daily_title

#~~~~~~~~~~~~~~~~~~~~~Growth Curve Plot~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("curve-plot", "figure"),
    [
        Input("country-dropdown2","value"),
        Input("days","value")
    ],
)
def display_growth_curve(country_dropdown,days):
    if country_dropdown=="World":
        cumux=cumu
    else:
        df0=[]
        for dataframe in rawdf[:3]:
            df0.append(dataframe[dataframe['Country/Region']==country_dropdown])
        sums=list(map(lambda x: sumbydate(x), df0))
        cumux=pd.DataFrame()
        cumux['date']=dates_real
        cumux['Confirmed']=sums[0].values
        cumux['Deaths']=sums[1].values
        cumux['Recovered']=sums[2].values
        cumux['Days']=np.arange(len(cumux))
        cumux['Days']+=1
        cumux['death_rate']=round(100*(cumux['Deaths']/cumux['Confirmed']),2)
        cumux['recover_rate']=round(100*(cumux['Recovered']/cumux['Confirmed']),2)
    if days=="":
        pred_period=5 #Number of days to plot ahead of today
    else:
        pred_period=int(days)
    days_count=len(dates)
    max_days=days_count+pred_period
    x=np.array(list(cumux['Days']))
    y=np.array(list(cumux['Confirmed']))
    popt, pcov = curve_fit(sigmoid_func, x, y,maxfev=100000)
    xx = np.linspace(1,max_days,max_days)
    yy = sigmoid_func(xx, *popt)
    init_date=datetime.datetime(2020,1,22)
    d=list()
    for i in range(max_days):
        d.append(init_date+datetime.timedelta(days=i))
    dd=np.array(d)
    del i, d
    figure=go.Figure(
        data=[
            go.Scatter(
                x=dd,
                y=y,
                mode='markers',
                name="Data",
                hovertemplate='Date: %{x}'+'<br>'+'Confirmed:'+'%{y}',
                marker=go.scatter.Marker(
                    color=orcl3[2]
                ),
                opacity=0.85,
            ),
            go.Scatter(
                x=dd,
                y=yy,
                mode='lines',
                name="Fit",
                hovertemplate='Date: %{x}'+'<br>'+'Fit:'+'%{y}',
                marker=go.scatter.Marker(
                    color='rgb(31, 119, 180)'
                ),
                opacity=0.85,   
            ),
        ],
        layout=dict(
            paper_bgcolor=bgcl,
            plot_bgcolor=bgcl,
            margin=dict(l=0, t=0, b=0, r=0, pad=0),
            xaxis=dict(
                zeroline=False,
                title='Date',
                showgrid=False,
                color=linecl,
            ),
            yaxis=dict(
                zeroline=False,
                title='Cumulative Confirmed Cases',
                showgrid=False,
                color=linecl,
            ),
            font=dict(
                family=plotfont, size=12, 
                color=fontcl,
            ),
            legend = dict(
                x=0.01, y=1
                )
        ),
    )
    return figure

#~~~~~~~~~~~~~~~~~~~~~New Cases Plot~~~~~~~~~~~~~~~~~~~~#
@app.callback(
    Output("bar-plot", "figure"),
    [
        Input("country-dropdown2","value"),
    ],
)
def display_new_cases(country_dropdown):
    if country_dropdown=="World":
        cumux=cumu
    else:
        df0=[]
        for dataframe in rawdf[:3]:
            df0.append(dataframe[dataframe['Country/Region']==country_dropdown])
        sums=list(map(lambda x: sumbydate(x), df0))
        cumux=pd.DataFrame()
        cumux['date']=dates_real
        cumux['Confirmed']=sums[0].values
        cumux['Deaths']=sums[1].values
        cumux['Recovered']=sums[2].values
        cumux['Days']=np.arange(len(cumux))
        cumux['Days']+=1
        cumux['death_rate']=round(100*(cumux['Deaths']/cumux['Confirmed']),2)
        cumux['recover_rate']=round(100*(cumux['Recovered']/cumux['Confirmed']),2)
    pred_period=5 #Number of days to plot ahead of today
    days_count=len(dates)
    max_days=days_count+pred_period
    #x=np.array(list(cumux['Days']))
    y=np.array(list(cumux['Confirmed']))
    y_prev=np.append(np.array([0,]), y[:days_count-1])
    y_change=y-y_prev
    init_date=datetime.datetime(2020,1,22)
    d=list()
    for i in range(max_days):
        d.append(init_date+datetime.timedelta(days=i))
    dd=np.array(d)
    del i, d
    figure=go.Figure(
        data=go.Bar(
            x=dd[:days_count],
            y=y_change,
            name="New Cases",
            hovertemplate='%{y} on %{x}',
            marker=dict(
                color=markercl,
                line=dict(
                    width=0,
                )
            ),
            opacity=0.85,
        ),
        layout=dict(
            paper_bgcolor=bgcl,
            plot_bgcolor=bgcl,
            margin=dict(l=0, t=0, b=0, r=0, pad=0),
            font=dict(
                family=plotfont,
                size=12,
                color=fontcl,
            ),
            xaxis=dict(
                zeroline=False,
                title='Date',
                showgrid=False,
                color=linecl,
            ),
            yaxis=dict(
                zeroline=False,
                title='New Confirmed Cases',
                showgrid=False,
                color=linecl,
            ),
        ),
    )
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)