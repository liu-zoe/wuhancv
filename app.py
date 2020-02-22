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
import datetime
from datetime import datetime

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
sheetnames=[
    "01-22-2020","01-23-2020","01-24-2020",
    "01-25-2020","01-26-2020","01-27-2020",
    "01-28-2020","01-29-2020","01-30-2020",
    "01-31-2020","02-01-2020","02-02-2020",
    "02-03-2020","02-04-2020","02-05-2020",
    "02-06-2020","02-07-2020","02-08-2020",
    "02-09-2020","02-10-2020","02-11-2020",
    "02-12-2020","02-13-2020","02-14-2020",
    "02-15-2020","02-16-2020","02-17-2020",
    "02-18-2020","02-19-2020","02-20-2020",
    "02-21-2020",
]
df=list(map(lambda x: pd.read_csv(os.path.join(APP_PATH, 'data/')+x+".csv"), sheetnames))
dates=[]
for dat in df:
    dates.append(dat['date'][0])
del dat

#Skip some dates to reduce the clutter
skip=1
newdates=[]
newdf=[]
i=len(dates)-1
while (i>=0):
    newdates.append(dates[i])
    newdf.append(df[i])
    i-=(skip+1)
newdates.reverse()
newdf.reverse()
dates=newdates
df=newdf
del skip, i, newdates, newdf

latlnt=pd.read_excel(os.path.join(APP_PATH, 'data/latlnt.xlsx'), usecols='A:D')
latlnt=latlnt.fillna(value={'State':''})

def cleandat(
    indat,
):
    indat=indat[['Province/State', 'Country/Region', 'Last Update', \
        'Confirmed', 'Deaths', 'Recovered','date'
    ]]
    indat.columns=['State','Country','Last Update','Confirmed','Deaths','Recovered','date']
    indat=indat.fillna(value={'State':'', 'Confirmed':0, \
        'Deaths':0, 'Recovered':0,})
    indat['Confirmed']=indat['Confirmed'].astype('int64')
    indat['Recovered']=indat['Recovered'].astype('int64')
    indat['Deaths']=indat['Deaths'].astype('int64')
    indat['Country']=np.where(indat['Country']=='US', "United States", 
                                np.where(indat['Country']=='Mainland China', "China", 
                                indat['Country']))
    indat['Country']=indat['Country'].str.strip()
    indat['State']=np.where( (indat['State']=='Hong Kong') & (indat['Country']=='Hong Kong'), '',
                    np.where( (indat['State']=='Taiwan') & (indat['Country']=='Taiwan'), '',
                    np.where( (indat['State']=='Macau') & (indat['Country']=='Macau'), '',
                    np.where( indat['State']=='Cruise Ship', 'Diamond Princess cruise ship',
                    np.where(indat['State']=='Chicago', 'Chicago, IL',
                    np.where( (indat['State']=='None') & (indat['Country']=='Lebanon'), '',
                    indat['State']))))))
    indat['State']=indat['State'].str.strip()
    indat['Location']=np.where(indat['State']=='', indat['Country'],\
        indat['Country']+'-'+indat['State'])
    indat=pd.merge(indat, latlnt, how='left', on=['Country','State'])
    indat['conf']=indat['Confirmed'].apply(lambda x: (math.log10(x+1))*13 if x>0 else 0)
    return indat
df=list(map(lambda x: cleandat(x), df))

# Create a dataset with cumulated cases by date
cum=pd.DataFrame(map(lambda x: [x.Confirmed.sum(), x.Deaths.sum(), x.Recovered.sum(),], df))
cum['date']=dates
cum.columns=['Confirmed','Deaths','Recovered','date']
cum['death_rate']=round(100*(cum['Deaths']/cum['Confirmed']),2)
cum['recover_rate']=round(100*(cum['Recovered']/cum['Confirmed']),2)
vars=['Confirmed','Deaths','Recovered', 'death_rate','recover_rate']
yaxislab=['Confirmed Cases', 'Deaths Cases', 'Recovered Cases',
'Death Rates (%)', 'Recovered Rates (%)']
charttitle=['Number of Confirmed Cases', 'Number of Deaths Cases', 
'Number of Recovered Cases', 'Deaths Rates', 'Recovered Rates']
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
app.title='COVID-19 Time Lapse'
#----------------------------------App Layout-----------------------------------#
app.layout = html.Div(
    id="root",
    children=[
        #Header
        html.Div(
            id="header",
            children=[
                html.Img(id="logo", src=app.get_asset_url("logo.png")),
                html.H3(children="Novel Coronavirus Outbreak Time Lapse",
                style={'textAlign': 'left',},
                ),
                dcc.Markdown(
                    id="description",
                    children=
                    '''
                    Data Source: Data used in this project is extracted from 
                    [**Mapping 2019-nCoV**](https://systems.jhu.edu/research/public-health/ncov/) 
                    by Johns Hopkins University Center Center for Systems Science and Engineering, 
                    who collected data from various sources, including WHO, U.S. CDC, ECDC China CDC (CCDC), 
                    NHC and DXY.                    
                    '''),
            ],
        ),
        #app
        html.Div(
            id="app-container", 
            children=[
                #Left Column
                html.Div(
                    id="left-column", 
                    children=[
                        html.Div(
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
                                    interval=2*1000, # in milliseconds
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
                                        for date_ord in range(len(dates))
                                    },
                                ),
                            ],
                        ),
                        html.Div(
                            id="bubblemap-container",
                            children=[
                                html.H5(
                                    "Confirmed COVID-19 Cases Across The Globe ",
                                    id="bubblemap-title",
                                    style={'textAlign': 'left',},
                                ),
                                dcc.Graph(
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
                    id="graph-container",
                    children=[
                        html.P(id="chart-selector", 
                                children="Select Type of Cases:", 
                                style={'textAlign': 'left',},
                        ), 
                        dcc.Dropdown(
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
                            value=0,
                            id="chart-dropdown",
                        ),
                        html.H5("Number of Confirmed Cases Across Time",
                                id="lineplot-title",
                                style={'textAlign': 'left',},
                                ),

                        dcc.Graph(
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
                                    ),
                                    font=dict(
                                        family=plotfont, size=12, 
                                        color=fontcl,
                                    ),
                                ),
                            ),
                        ),
                    ],
                ),
            ],
        ),
        #Footer
        html.Div(
            id="footer",
            children=[
                html.H5(
                    [
                        "Create by ",
                        html.A("Zoe Liu", href="http://zoe-liu.com", target="_blank"),
                    ]
                ),
                dcc.Markdown(
                    id="credit",
                    children=
                    '''
                    **Credit:** style and set-up is mostly based on the Dash sample app 
                    [*US Opiod Epidemic*](https://dash-gallery.plotly.host/dash-opioid-epidemic/).
                    '''),
            ],
        ),
    ],
)
#----------------------------------Callback-----------------------------------#
#~~~~~~~~~~~~Bubble Plot Slider~~~~~~~~~~~#
@app.callback(
    Output("country-bubble", "figure"), 
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
    return fig

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
    Output("lineplot-title", "children"), 
    [
        Input("chart-dropdown", "value"),
    ],
)
def update_chart_title(chart_dropdown):
    return charttitle[chart_dropdown]+" Across Time"

@app.callback(
    Output("selected-data", "figure"),
    [
        Input("chart-dropdown","value"),
    ],
)
def display_selected_data(chart_dropdown):
    fig=go.Figure(
        data=go.Scatter(
            x=cum['date'],
            y=cum[vars[chart_dropdown]],
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
                    tickangle=45,
        ),
        font=dict(
            family=plotfont, 
            size=11, 
            color=fontcl,
        ),
    )
    return fig 

if __name__ == '__main__':
    app.run_server(debug=True)

# %%
