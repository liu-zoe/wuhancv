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

# Initialize app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"},
        {"name": "description", "content": "A Time Lapse of the 2019-nCoV Outbreak"}, 
        {"name": "news_keywords", "content": "2019-nCoV, Novel Coronavirus, Novel CoronaVirus, Wuhan Coronavirus"}
        ],
    )
server=app.server
#--------------------------Load Data-----------------------------------#
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
filename='data/WHCV_JHU.xlsx'
sheetnames=['Jan22_12pm', 'Jan23_12pm', 'Jan24_12pm',
'Jan25_10pm', 'Jan26_11pm', 'Jan27_830pm',
'Jan28_11pm', 'Jan29_9pm', 'Jan30_930pm',
'Jan31_7pm','Feb01_11pm', 'Feb02_9pm',
'Feb03_940pm','Feb04_10pm','Feb05_1220pm',
'Feb06_0805pm',
]
# Create a list of dates
dates=['Jan22','Jan23','Jan24',
'Jan25','Jan26','Jan27',
'Jan28','Jan29','Jan30',
'Jan31','Feb01','Feb02',
'Feb03','Feb04','Feb05',
'Feb06',
]
xlsxf=pd.ExcelFile(
    os.path.join(APP_PATH, filename)
    )
df=list(map(lambda x: xlsxf.parse(x), sheetnames))
latlnt=pd.read_excel(os.path.join(APP_PATH, 'data/latlnt.xlsx'), usecols='A:D')
latlnt=latlnt.fillna(value={'State':''})

def cleandat(
    indat,
):
    indat=indat.fillna(value={'State':'', 'Confirmed':0, \
        'Recovered':0, 'Deaths':0})
    indat['Confirmed']=indat['Confirmed'].astype('int64')
    indat['Recovered']=indat['Recovered'].astype('int64')
    indat['Deaths']=indat['Deaths'].astype('int64')
    indat['Country']=np.where(indat['Country']=='US', "United States", 
                                np.where(indat['Country']=='Mainland China', "China", 
                                indat['Country']))
    indat['State']=np.where( (indat['State']=='Hong Kong') & (indat['Country']=='Hong Kong'), '',
                    np.where( (indat['State']=='Taiwan') & (indat['Country']=='Taiwan'), '',
                    np.where( (indat['State']=='Macau') & (indat['Country']=='Macau'), '',
                    indat['State'])))
    indat['Location']=np.where(indat['State']=='', indat['Country'],\
        indat['Country']+'-'+indat['State'])
    indat=pd.merge(indat, latlnt, how='left', on=['Country','State'])
    indat['conf']=indat['Confirmed'].apply(lambda x: (math.log10(x+1))*10 if x>0 else 0)
    indat['date']=indat['Last Update'].apply(lambda x: x.date())
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
app.title='2019-nCoV Time Lapse'
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
                                html.P(
                                    id="slider-text", 
                                    children="Move the slider to advance date:",
                                    style={'textAlign': 'left',},
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
                                    "Coronavirus Cases Across The Globe ",
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
                                            hovertext =df[0]['Location']+ '<br> Confirmed:' + df[0]['Confirmed'].astype(str),
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
            hovertext =filtered_df['Location']+ '<br> Confirmed:' + filtered_df['Confirmed'].astype(str),
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
