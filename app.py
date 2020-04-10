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
#--------------------------Load Data-----------------------------------#
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
init_date=datetime.datetime(2020,1,22)
sheetnames=list()
for i in range(79): #<-Update the range number everyday
    x=dt.strftime(init_date+datetime.timedelta(days=i),'%m-%d-%Y')
    sheetnames.append(x)
del i,x
df=list(map(lambda x: pd.read_csv(os.path.join(APP_PATH, 'data/')+x+".csv"), sheetnames))
dates=[]
for dat in df:
    dates.append(dat['date'][0])
del dat
bubble_size_index=7
# Create a dataset with ISO FIPS and latitude/longitude data
lookup=pd.read_csv(os.path.join(APP_PATH, 'data/')+'UID.csv')
lookup_us_county=lookup[(lookup['Country_Region']=='US') & (lookup['FIPS']>0) &\
     (lookup['Admin2'].isnull()==0) & (lookup['Lat'].isnull()==0)]
lookup_us_county=lookup_us_county[['iso2','iso3','FIPS','Admin2','Province_State','Lat','Long_', 'Combined_Key']]
del lookup
USlatlnt=pd.read_excel(os.path.join(APP_PATH, 'data/US_latlnt.xlsx'), usecols='A:D')
def cleandat(
    indat,
):
    indat=indat[['Province/State', 'Country/Region', 'Last Update', \
        'Confirmed', 'Deaths', 'Recovered', 'Latitude','Longitude',\
        'date', 'year', 'month', 'day'
    ]]
    indat.columns=['State','Country','Last Update',\
    'Confirmed','Deaths','Recovered','lat', 'long',\
    'date','year', 'month', 'day']
    indat=indat.fillna(value={'State':'', 'Confirmed':0, \
        'Deaths':0, 'Recovered':0,})
    indat['Confirmed']=indat['Confirmed'].astype('int64')
    indat['Recovered']=indat['Recovered'].astype('int64')
    indat['Deaths']=indat['Deaths'].astype('int64')
    indexNames=indat[(indat['Confirmed']==0)&(indat['Recovered']==0)&(indat['Deaths']==0)].index
    indat.drop(indexNames , inplace=True)
    indat['Country']=indat['Country'].str.strip()
    indat['State']=indat['State'].str.strip()    
    indat['Country']=np.where(indat['Country']=='US', "United States", 
                                np.where(indat['Country']=='China', 'Mainland China',
                                np.where(indat['Country']=='Hong Kong SAR', 'Hong Kong',
                                np.where(indat['Country']=='Macao SAR', 'Macau',
                                np.where(indat['Country']=='Iran (Islamic Republic of)', 'Iran', 
                                np.where(indat['Country'].isin(['Korea, South','Republic of Korea']), 'South Korea',
                                np.where(indat['Country'].isin(['Taiwan*','Taipei and environs']), 'Taiwan',
                                np.where(indat['Country'].isin(['Russian Federation']), 'Russia',
                                np.where(indat['Country'].isin(['UK']), 'United Kingdom',
                                np.where(indat['Country'].isin(['Ivory Coast']), "Cote d'Ivoire",
                                np.where(indat['Country'].isin(['Viet Nam']), 'Vietnam',
                                indat['Country'])))))))))))
    indat['State']=np.where( (indat['State']=='Hong Kong') & (indat['Country']=='Hong Kong'), '',
                    np.where( (indat['State']=='Taiwan') & (indat['Country']=='Taiwan'), '',
                    np.where( (indat['State']=='Macau') & (indat['Country']=='Macau'), '',
                    np.where( indat['State']=='Cruise Ship', 'Diamond Princess cruise ship',
                    np.where(indat['State']=='Chicago', 'Chicago, IL',
                    np.where( (indat['State']=='None') & (indat['Country'].isin(['Lebanon','Iraq','Austria'])), '',
                    indat['State']))))))
    indat=indat[indat['State'].isin(['Recovered'])==0]
    indat['Location']=np.where(indat['State']=='Wuhan Evacuee', 'United States-Wuhan Evacuee', 
                      np.where(indat['State']=='', indat['Country'],\
                          indat['Country']+'-'+indat['State']))
    #Redefine locations for cruises
    indat['lat']=np.where(indat['Location']=='Australia-From Diamond Princess', -29.863278,
                 np.where(indat['Location']=='Canada-Diamond Princess', 62.454715,
                 np.where(indat['Location']=='Canada-Grand Princess', 61.962982,
                 np.where(indat['Location'].isin(['United States-Grand Princess', 'United States-Grand Princess Cruise Ship']), 41.317397, 
                 np.where(indat['Location']=='United States-Diamond Princess', 38.529235, 
                 np.where(indat['State']=='Wuhan Evacuee', 36.921770, 
                 np.where(indat['Location']=='United States-Unassigned Location (From Diamond Princess)', 37.98,
                 indat['lat']
                 )))))))
    indat['long']=np.where(indat['Location']=='Australia-From Diamond Princess', 158.162512, 
                  np.where(indat['Location']=='Canada-Diamond Princess', -89.830242,
                  np.where(indat['Location']=='Canada-Grand Princess', -91.917644, 
                  np.where(indat['Location'].isin(['United States-Grand Princess', 'United States-Grand Princess Cruise Ship']), -127.942490, 
                  np.where(indat['Location']=='United States-Diamond Princess', -126.832871, 
                  np.where(indat['State']=='Wuhan Evacuee',-124.399399,
                  np.where(indat['Location']=='United States-Unassigned Location (From Diamond Princess)', -125.87,
                  indat['long']
                  )))))))
    indat['conf']=indat['Confirmed'].apply(lambda x: (math.log10(x+1))*bubble_size_index if x>0 else 0)
    return indat
df=list(map(lambda x: cleandat(x), df))

#Create a subset of all dates to limit the clutter on bubblemap timetrack
skip=1
mark_index=[]
i=len(dates)-1
while (i>=0):
    mark_index.append(i)
    i-=(skip+1)
mark_index.reverse()
del skip, i

# Create a dataset with cumulated cases by date
cum=pd.DataFrame(map(lambda x: [x.Confirmed.sum(), x.Deaths.sum(), x.Recovered.sum(),], df))
cum['date']=dates
cum['Days']=np.arange(len(cum))
cum['Days']+=1
cum.columns=['Confirmed','Deaths','Recovered','date','Days']
cum['death_rate']=round(100*(cum['Deaths']/cum['Confirmed']),2)
cum['recover_rate']=round(100*(cum['Recovered']/cum['Confirmed']),2)
vars=['Confirmed','Deaths','Recovered', 'death_rate','recover_rate']
yaxislab=['Confirmed Cases', 'Deaths Cases', 'Recovered Cases',
'Death Rates (%)', 'Recovered Rates (%)']
charttitle=['Number of Confirmed Cases Across Time', 
'Number of Deaths Cases Across Time', 
'Number of Recovered Cases Across Time', 
'Deaths Rates* Across Time', 
'Recovered Rates Across Time']

#----------------------------------Load NYT Data-------------------------------#
# New York Times Data
#https://github.com/nytimes/covid-19-data
nyt_state=pd.read_csv(os.path.join(APP_PATH, 'data/NYT/us-states.csv'))
dates_nyt0=list(set(nyt_state['date']))
dates_nyt0.sort()
dates_nyt1=pd.DataFrame(dates_nyt0)
dates_nyt1.columns=['date']
dates_nyt1['stamp']=dates_nyt1['date'].apply(lambda x: (dt.strptime(x, '%Y-%m-%d')))
dates_nyt1['date2']=dates_nyt1['stamp'].apply(lambda x: (dt.strftime(x, '%b%d')))
dates_nyt=list(dates_nyt1['date2'])
del dates_nyt0, dates_nyt1
nyt_state['stamp']=nyt_state['date'].apply(lambda x: (dt.strptime(x, '%Y-%m-%d')))
nyt_state['date2']=nyt_state['stamp'].apply(lambda x: (dt.strftime(x, '%b%d')))
nyt_state=nyt_state[['date','state','fips','cases','deaths']]
nyt_state.columns=['date','state','fips','Confirmed','Deaths']

nyt_county_tmp=pd.read_csv(os.path.join(APP_PATH, 'data/NYT/us-counties.csv'))
nyt_county_tmp['stamp']=nyt_county_tmp['date'].apply(lambda x: (dt.strptime(x, '%Y-%m-%d')))
nyt_county_tmp['date2']=nyt_county_tmp['stamp'].apply(lambda x: (dt.strftime(x, '%b%d')))
nyt_county_tmp=nyt_county_tmp[['date2','county','state','fips','cases','deaths']]
nyt_county_tmp.columns=['date','county','state','fips','Confirmed','Deaths']
nyt_county_tmp=pd.merge(nyt_county_tmp, lookup_us_county, how='left',left_on='fips',right_on='FIPS')
nyt_county_tmp.columns=['date','county','state','fips','Confirmed','Deaths',\
    'iso2','ios3','FIPS','Admin2','Province/State','lat','long','Combined_Key']
nyt_county_tmp['lat']=np.where(nyt_county_tmp['county']=='New York City', 40.7128, 
                      np.where(nyt_county_tmp['county']=='Kansas City', 39.0997, nyt_county_tmp['lat']))
nyt_county_tmp['long']=np.where(nyt_county_tmp['county']=='New York City', -74.0060, 
                      np.where(nyt_county_tmp['county']=='Kansas City', -94.5786, nyt_county_tmp['long']))
nyt_county1=nyt_county_tmp[nyt_county_tmp['lat'].isnull()==0]
nyt_county2=nyt_county_tmp[(nyt_county_tmp['lat'].isnull()==1) & (nyt_county_tmp['county']=='Unknown')]
nyt_county2=pd.merge(nyt_county2, USlatlnt, how='left',left_on='state',right_on='Province_State')
nyt_county2['lat']=nyt_county2['Latitude']
nyt_county2['long']=nyt_county2['Longitude']
nyt_county2=nyt_county2.drop(['Province_State','Country_Region','Latitude','Longitude'],axis=1)
nyt_county=pd.concat([nyt_county1,nyt_county2])
del nyt_county_tmp, nyt_county1, nyt_county2
nyt_county['Confirmed']=nyt_county['Confirmed'].astype('int64')
nyt_county['Deaths']=nyt_county['Deaths'].astype('int64')
nyt_county=nyt_county.fillna(value={'Confirmed':0, 'Deaths':0})
nyt_county['conf']=nyt_county['Confirmed'].apply(lambda x: (math.log10(x+1))*bubble_size_index if x>0 else 0)
nyt_county['Combined_Key']=np.where(nyt_county['Combined_Key'].isnull(), nyt_county['state']+'-'+nyt_county['county'], \
        nyt_county['Combined_Key'])
nyt_county_0=nyt_county[nyt_county['date']=='Jan21']

skip_nyt=1
mark_index_nyt=[]
i=len(dates_nyt)-1
while (i>=0):
    mark_index_nyt.append(i)
    i-=(skip_nyt+1)
mark_index_nyt.reverse()
del skip_nyt, i
#----------------------------------Fit a growth curve-------------------------------#
pred_period=5 #Number of days to plot ahead of today
days_count=len(dates)
max_days=days_count+pred_period
x=np.array(list(cum['Days']))
y=np.array(list(cum['Confirmed']))
y_prev=np.array([0,])
y_prev=np.append(y_prev, y[:days_count-1])
y_change=y-y_prev
def sigmoid_func(x, a, k, delta, L):
    y=a+((L-a)/(1+np.exp((k-x)/delta)))
    return y
popt, pcov = curve_fit(sigmoid_func, x, y,maxfev=100000)
xx = np.linspace(1,max_days,max_days)
yy = sigmoid_func(xx, *popt)
#init_date=datetime.datetime(2020,1,22)
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
                        Data Source: Data used in Global Outbreak Map and Growth Curve is extracted from 
                        [**Mapping 2019-nCoV**](https://www.arcgis.com/apps/opsdashboard/index.html#/bda7594740fd40299423467b48e9ecf6) 
                        by [Johns Hopkins University Center Center for Systems Science and Engineering](https://systems.jhu.edu/research/public-health/ncov/), 
                        who collected data from various sources, including WHO, U.S. CDC, ECDC China CDC (CCDC), 
                        NHC and DXY. 
                        Data used in US Outbreak Map is based on data released by [New York Time](https://github.com/nytimes/covid-19-data)
                        due to lack of county-level data from Johns Hopkins University between Jan 22 and Mar 22.                   
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
                                                dcc.Interval(id='auto-stepper',
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
                                                            "label":dates[date_ord],
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
                                                    "Confirmed COVID-19 Cases Across The Globe on Jan 22",
                                                    className="bubblemap-title",
                                                    id="bubblemap-title",
                                                    style={'textAlign': 'left',},
                                                ),
                                                dcc.Graph(
                                                    className="country-bubble", 
                                                    id="country-bubble",
                                                    figure = go.Figure(
                                                        data=go.Scattergeo(
                                                            lat = df[0]['lat'],
                                                            lon = df[0]['long'],
                                                            mode='markers',
                                                            hovertext =df[0]['Location']\
                                                            + '<br> Confirmed:' + df[0]['Confirmed'].astype(str)\
                                                            + '<br> Deaths:' + df[0]['Deaths'].astype(str)\
                                                            + '<br> Recovered:' + df[0]['Recovered'].astype(str),
                                                            marker = go.scattergeo.Marker(
                                                                color = markercl,
                                                                size = df[0]['conf'],
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
                                                            "value":"United States"
                                                        },
                                                        {
                                                            "label":"Italy",
                                                            "value":"Italy",
                                                        },
                                                        {
                                                            "label":"Spain",
                                                            "value":"Spain",
                                                        },
                                                        {
                                                            "label":"Mainland China",
                                                            "value":"Mainland China",
                                                        },
                                                        {                                                                                                                
                                                            "label":"Germany",
                                                            "value":"Germany",
                                                        },
                                                        {
                                                            "label":"France",
                                                            "value":"France",
                                                        },
                                                        {
                                                            "label":"Iran",
                                                            "value":"Iran",
                                                        },
                                                        {
                                                            "label":"United Kingdom",
                                                            "value":"United Kingdom",
                                                        },
                                                        {
                                                            "label":"Turkey",
                                                            "value":"Turkey",
                                                        },                                                        
                                                        {
                                                            "label":"Switzerland",
                                                            "value":"Switzerland",
                                                        },
                                                        {
                                                            "label":"Belgium",
                                                            "value":"Belgium",                                                        
                                                        },
                                                        {
                                                            "label":"Netherlands",
                                                            "value":"Netherlands",                                                        
                                                        },
                                                        {
                                                            "label":"Canada",
                                                            "value":"Canada",                                                        
                                                        },                                                        
                                                        {
                                                            "label":"Austria",
                                                            "value":"Austria",                                                        
                                                        },
                                                        {
                                                            "label":"Portugal",
                                                            "value":"Portugal",                                                        
                                                        },
                                                        {
                                                            "label":"South Korea",
                                                            "value":"South Korea",
                                                        },
                                                        {
                                                            "label":"Brazil",
                                                            "value":"Brazil",                                                        
                                                        },
                                                        {
                                                            "label":"Israel",
                                                            "value":"Israel",                                                        
                                                        },                                    
                                                        {
                                                            "label":"Sweden",
                                                            "value":"Sweden",                                                        
                                                        },
                                                        {
                                                            "label":"Australia",
                                                            "value":"Australia",                                                        
                                                        },
                                                        {
                                                            "label":"Norway",
                                                            "value":"Norway",                                                        
                                                        },
                                                        {
                                                            "label":"Japan",
                                                            "value":"Japan",
                                                        },
                                                        {
                                                            "label":"Singapore",
                                                            "value":"Singapore",
                                                        },
                                                        {
                                                            "label":"Taiwan",
                                                            "value":"Taiwan",
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
                                        html.H5("Number of Confirmed Cases Across Time",
                                                id="lineplot-title",
                                                style={'textAlign': 'left',},
                                                ),
                                        dcc.Graph(
                                            className="selected-data",
                                            id="selected-data",
                                            figure=go.Figure(
                                                data=go.Scatter(
                                                    x=cum['date'],
                                                    y=cum['Confirmed'],
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
                                                    interval=1*1000, # in milliseconds
                                                    n_intervals=0,
                                                    max_intervals=0,
                                                    disabled=False,
                                                ),
                                                dcc.Slider(
                                                    id="date-slider-us",
                                                    min=0, 
                                                    max=len(dates_nyt)-1,
                                                    value=0,
                                                    marks={
                                                        str(date_ord):{
                                                            "label":dates_nyt[date_ord],
                                                            "style": {"transform": "rotate(45deg)"}
                                                        } 
                                                        for date_ord in mark_index_nyt
                                                    },
                                                ),
                                            ],
                                        ),
                                        html.Div(
                                            className="bubblemap-container",
                                            children=[
                                                html.H5(
                                                    "Confirmed COVID-19 Cases in the US on Jan 21",
                                                    className="bubblemap-title",
                                                    id="bubblemap-title-us",
                                                    style={'textAlign': 'left',},
                                                ),
                                                dcc.Graph(
                                                    className="country-bubble", 
                                                    id="country-bubble-us",
                                                    figure = go.Figure(
                                                        data=go.Scattergeo(
                                                            lat = nyt_county_0['lat'],
                                                            lon = nyt_county_0['long'],
                                                            mode='markers',
                                                            hovertext =nyt_county_0['Combined_Key']\
                                                            + '<br> Confirmed:' + nyt_county_0['Confirmed'].astype(str)\
                                                            + '<br> Deaths:' + nyt_county_0['Deaths'].astype(str),
                                                            marker = go.scattergeo.Marker(
                                                                color = markercl,
                                                                size = nyt_county_0['conf'],
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
                                                    value="USA",
                                                    className="country-dropdown",
                                                    id="country-dropdown-us",
                                                    options=[                                                
                                                        {
                                                            "label":"USA",
                                                            "value":"USA",
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
                                        html.H5("Number of Confirmed Cases Across Time",
                                                id="lineplot-title-us",
                                                style={'textAlign': 'left',},
                                                ),
                                        dcc.Graph(
                                            className="selected-data",
                                            id="selected-data-us",
                                            figure=go.Figure(
                                                data=go.Scatter(
                                                    x=nyt_state['date'],
                                                    y=nyt_state['Confirmed'],
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
                                                            "value":"United States"
                                                        },
                                                        {
                                                            "label":"Italy",
                                                            "value":"Italy",
                                                        },
                                                        {
                                                            "label":"Spain",
                                                            "value":"Spain",
                                                        },
                                                        {
                                                            "label":"Mainland China",
                                                            "value":"Mainland China",
                                                        },
                                                        {                                                                                                                
                                                            "label":"Germany",
                                                            "value":"Germany",
                                                        },
                                                        {
                                                            "label":"France",
                                                            "value":"France",
                                                        },
                                                        {
                                                            "label":"Iran",
                                                            "value":"Iran",
                                                        },
                                                        {
                                                            "label":"United Kingdom",
                                                            "value":"United Kingdom",
                                                        },
                                                        {
                                                            "label":"Turkey",
                                                            "value":"Turkey",
                                                        },                                                        
                                                        {
                                                            "label":"Switzerland",
                                                            "value":"Switzerland",
                                                        },
                                                        {
                                                            "label":"Belgium",
                                                            "value":"Belgium",                                                        
                                                        },
                                                        {
                                                            "label":"Netherlands",
                                                            "value":"Netherlands",                                                        
                                                        },
                                                        {
                                                            "label":"Canada",
                                                            "value":"Canada",                                                        
                                                        },                                                        
                                                        {
                                                            "label":"Austria",
                                                            "value":"Austria",                                                        
                                                        },
                                                        {
                                                            "label":"Portugal",
                                                            "value":"Portugal",                                                        
                                                        },
                                                        {
                                                            "label":"South Korea",
                                                            "value":"South Korea",
                                                        },
                                                        {
                                                            "label":"Brazil",
                                                            "value":"Brazil",                                                        
                                                        },
                                                        {
                                                            "label":"Israel",
                                                            "value":"Israel",                                                        
                                                        },                                    
                                                        {
                                                            "label":"Sweden",
                                                            "value":"Sweden",                                                        
                                                        },
                                                        {
                                                            "label":"Australia",
                                                            "value":"Australia",                                                        
                                                        },
                                                        {
                                                            "label":"Norway",
                                                            "value":"Norway",                                                        
                                                        },
                                                        {
                                                            "label":"Japan",
                                                            "value":"Japan",
                                                        },
                                                        {
                                                            "label":"Singapore",
                                                            "value":"Singapore",
                                                        },
                                                        {
                                                            "label":"Taiwan",
                                                            "value":"Taiwan",
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
                                        html.H5("Cumulative Confirmed Cases with Fitted Curve in United States",
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
                                            children="Daily New Confirmed Cases in United States",
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
    filtered_df=df[date_index]

    fig = go.Figure(
        data=go.Scattergeo(
            lat = filtered_df['lat'],
            lon = filtered_df['long'],
            mode='markers',
            hovertext =filtered_df['Location']+ '<br> Confirmed:' + filtered_df['Confirmed'].astype(str)\
                                              + '<br> Deaths:' + filtered_df['Deaths'].astype(str)\
                                              + '<br> Recovered:' + filtered_df['Recovered'].astype(str),
            marker = go.scattergeo.Marker(
                    color = markercl,
                    size = filtered_df['conf'],
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
    return fig, "Confirmed COVID-19 Cases Across The Globe on "+dates[date_index]

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
        cum0=cum
    else:
        df0=[]
        for dataframe in df:
            df0.append(dataframe[dataframe['Country']==country_dropdown])
        cum0=pd.DataFrame(map(lambda x: [x.Confirmed.sum(), x.Deaths.sum(), x.Recovered.sum(),], df0))
        cum0['date']=dates
        cum0.columns=['Confirmed','Deaths','Recovered','date']
        cum0['death_rate']=round(100*(cum0['Deaths']/cum0['Confirmed']),2)
        cum0['recover_rate']=round(100*(cum0['Recovered']/cum0['Confirmed']),2)
    yvar=vars[chart_dropdown]
    cum_one_var=cum0[cum0[yvar]>0][['date', yvar]]
    fig=go.Figure(
        data=go.Scatter(
            x=cum_one_var['date'],
            y=cum_one_var[yvar],
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
    #filtered_df=dfus[date_index]
    filtered_df=nyt_county[nyt_county['date']==dates_nyt[date_index]]
    fig = go.Figure(
        data=go.Scattergeo(
            lat = filtered_df['lat'],
            lon = filtered_df['long'],
            mode='markers',
            hovertext =filtered_df['Combined_Key']+'<br> Confirmed:'+filtered_df['Confirmed'].astype(str)\
                                              + '<br> Deaths:' + filtered_df['Deaths'].astype(str),
            marker = go.scattergeo.Marker(
                    color = markercl,
                    size = filtered_df['conf'],
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
    return fig, "Confirmed COVID-19 Cases in the US on "+dates_nyt[date_index]

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
        slider_value=(n_intervals+1)%(len(dates_nyt))
        max_intervals=-1
        int_disabled=False
    elif (pause_timestamp>play_timestamp):
        slider_value=(n_intervals+1)%(len(dates_nyt))
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
    if state_dropdown=="USA":
        cum0=nyt_state.groupby(['date'])[['Confirmed','Deaths']].sum().reset_index()
        cum0.columns=['date','Confirmed','Deaths']
        cum0['death_rate']=round(100*(cum0['Deaths']/cum0['Confirmed']),2)
    else:
        df0=nyt_county[nyt_county['Province/State']==state_dropdown]
        cum0=df0.groupby(['date'])[['Confirmed','Deaths']].sum().reset_index()
        cum0.columns=['date','Confirmed','Deaths']
        cum0['death_rate']=round(100*(cum0['Deaths']/cum0['Confirmed']),2)
        cum0['date2']=cum0['date'].apply(lambda x:(dt.strptime('2020'+x, '%Y%b%d')))
        cum0=cum0.sort_values(by=['date2']).reset_index()
    yvar=vars[chart_dropdown]
    cum_one_var=cum0[cum0[yvar]>0][['date', yvar]]
    fig=go.Figure(
        data=go.Scatter(
            x=cum_one_var['date'],
            y=cum_one_var[yvar],
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
        cum0=cum
    else:
        df0=[]
        for dataframe in df:
            df0.append(dataframe[dataframe['Country']==country_dropdown])
        cum0=pd.DataFrame(map(lambda x: [x.Confirmed.sum(),], df0))
        cum0.columns=['Confirmed',]
        cum0['Days']=np.arange(len(cum0))
        cum0['Days']+=1
    if days=="":
        pred_period=5 #Number of days to plot ahead of today
    else:
        pred_period=int(days)
    days_count=len(dates)
    max_days=days_count+pred_period
    x=np.array(list(cum0['Days']))
    y=np.array(list(cum0['Confirmed']))
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
        cum0=cum
    else:
        df0=[]
        for dataframe in df:
            df0.append(dataframe[dataframe['Country']==country_dropdown])
        cum0=pd.DataFrame(map(lambda x: [x.Confirmed.sum(),], df0))
        cum0.columns=['Confirmed',]
        cum0['Days']=np.arange(len(cum0))
        cum0['Days']+=1
    pred_period=5 #Number of days to plot ahead of today
    days_count=len(dates)
    max_days=days_count+pred_period
    x=np.array(list(cum0['Days']))
    y=np.array(list(cum0['Confirmed']))
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