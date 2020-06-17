#%% [markdown]
## Project Name: WUHANCV
### Program Name: CoronaV_Twitter_Clusters.py
### Purpose: To process Twitter Following data. 
##### Date Created: May 10th 2020
#### 
# Twint Documentation:https://github.com/twintproject/twint
#%%
from IPython import get_ipython
get_ipython().magic('reset -sf')
import datetime
from datetime import datetime as dt
from datetime import date
import os 
from os import listdir
from os.path import isfile, join
import pathlib
import colorlover as cl
import plotly.graph_objs as go
import chart_studio.plotly as py
import plotly.express as px
import pandas as pd
import numpy as np
import math
import re
import twint
import jgraph as jg
import ast
import functools
import operator
from collections import Counter
import json
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
#%%
t0=dt.now()
print('-------------------------Start Running Code------------------')
print('Time:', t0)
#%% 
# Styles
plotlycl=px.colors.qualitative.Plotly
orcl3=cl.scales['3']['seq']['Oranges']
grcl3=cl.scales['3']['seq']['Greys']
bgcl="#111"
linecl=grcl3[0]
fontcl="#eee"
markercl="#e7ad52"
plotfont="Open Sans, sans-serif"
#%%
# Reading in the Tweets from April 1st to 4th
datafiles=['5g_twitter_2020_04_01.csv', '5g_twitter_2020_04_02.csv', 
            '5g_twitter_2020_04_03.csv', '5g_twitter_2020_04_04.csv',
            '5g_twitter_2020_04_05.csv', '5g_twitter_2020_04_06.csv', 
            '5g_twitter_2020_04_07.csv', '5g_twitter_2020_04_08.csv',
            '5g_twitter_2020_04_09.csv',
            ]
dflst=list(
    map(
        lambda x: pd.read_csv(
            os.path.join(APP_PATH, 'data', 'Twitter', x),
            error_bad_lines=False,
            dtype={
                'id': int, 'conversation_id': int, 'created_at': int, 'date': object, 'time': object,
                'timezone': object, 'user_id': int, 'username': str, 'name': str, 'place': str,
                'tweet': str, 'mentions': object, 'urls': object, 'photos': object, 'replies_count': int,
                'retweets_count': int, 'likes_count': int, 'hashtags': str, 'cashtags': str,
                'link': str, 'reweet': bool, 'quote_url': str, 'video': int, 'near': float,
                'geo': float, 'source': float, 'user_rt_id': float, 'user_rt': float, 'retweet_id': float,
                'reply_to': object, 'retweet_date': float, 'translate': float, 'trans_src': float,
                'trans_dest': float,
            }
        ),
        datafiles
        )
    )
#%%
df=pd.concat(dflst)
del datafiles, dflst
# Drop columns that are not useful
df=df.drop(['retweet','near','geo','source','user_rt_id','user_rt','retweet_id','retweet_date','translate','trans_src','trans_dest'], axis=1)
# Drop duplicate rows; sort by retweet counts; and reset index
df.drop_duplicates(subset='link', keep='first',inplace=True)
df.sort_values('retweets_count', inplace=True, ascending=False)
df.reset_index(drop=True, inplace=True)
#%%
# Screen out posts that does not have the key words "corona", "virus", or "covid"
#df=df0[df0.tweet.str.contains('corona|virus|covid', flags=re.IGNORECASE)]
#%%
# Find the most freqeuent word
'''
import nltk
all_tweets=' '.join(list(df['tweet']))
stopwords = nltk.corpus.stopwords.words('english')
wt=[i.lower() for i in nltk.word_tokenize(all_tweets) if (i.isalnum()) & (i.lower() not in stopwords)]
freqwrd = Counter(wt)
#freqwrd.most_common(300)
pd.DataFrame.from_dict(freqwrd, orient="index").to_csv(os.path.join(APP_PATH, 'data', 'Twitter', 'tweet_word_frequency.csv'))
'''
#%%
# Create dictionary of username vs name
username_dict=dict(zip(df.username, df.name))
u_name=list(df['username'])
#%%
quote_url=list(df['quote_url'])
urls=list(map(lambda x: list(ast.literal_eval(x.lower())), list(df['urls'])))
#%%
reply_to=list(df['reply_to'])
reply_to_u=list(map(lambda x: list(pd.DataFrame(ast.literal_eval(x.lower()))['username']), reply_to))
#%%
mentions=list(map(lambda x: list(ast.literal_eval(x.lower())), list(df['mentions'])))
#%%
# Extract any additional data from reply_to, urls, quote_url columns
reacts_to=[] #The combination of mentions, reply to, quote_url, and urls
for i in range(len(mentions)):
    x=[]
    x1=mentions[i]
    x2=reply_to_u[i]
    x3=quote_url[i]
    x4=urls[i]
    x+=x1    
    x+=x2
    if isinstance(x3,str):
        x+=re.findall('twitter.com/([A-Za-z0-9]+)/status/[0-9]+', x3.lower())    
    if len(x4)>0:
        x4b=list(map(lambda x: re.findall('twitter.com/([A-Za-z0-9]+)/status/[0-9]+', x.lower()), x4))
        x4=list(set(functools.reduce(operator.iconcat, x4b,[])))
        x+=x4
    if u_name[i] in x:
        x.remove(u_name[i])
    x=list(set(x))
    reacts_to+=[x]        
del i, x, x1, x2, x3, x4, x4b
#%%
reacts_to2=[]
for i in range(len(reacts_to)):
    if len(reacts_to[i])>0:
        reacts_to2+=reacts_to[i]
del i
#%% 
# A function to insert line breaks
def break_tweets(
    t, # Text of the tweet
    length=72, # desired length of a line
):
    t_len = len(t)
    if t_len <= length:
        text = t+'<br>'
    else:
        text = ''
        t_list=t.split(' ')
        k=0
        m=0
        j=0
        while j<len(t_list):
            k += (len(t_list[j])+1)
            if (k>length) or (j==len(t_list)-1):
                text+=' '.join(t_list[m:j+1])
                text+='<br>'
                m=j+1
                k=0
            j+=1
    return(text)
#%% 
# Create nodes and labels
nodes_d=dict()
labels_d=dict()
for i in range(len(df)):
    currow=df.iloc[i]
    t=break_tweets(currow['tweet'])
    if type(currow['name'])==str:
        label=''.join([currow['name'],'(@',currow['username'],')','<br>', \
            t, currow['date'], ' ',currow['time']])
    else:
        label=''.join([currow['username'],'<br>', \
            t, currow['date'], ' ',currow['time']])
    labels_d[i]=label
    nodes_d[i]=currow['link']
del i, currow, label
#%%
# Create links
t_link=df.link
links=dict()
for i in range(len(df)):
    currow=df.iloc[i]
    if currow['conversation_id'] in conv_id_dict.keys():
        source=conv_id_dict[currow['conversation_id']]
        if source!=i:
            if source not in links.keys():
                links[source]=[i]
            elif i not in links[source]:
                links[source].append(i)
    if type(currow['quote_url'])==str:
        if currow['quote_url'] in t_link:        
            source=t_link[t_link==currow['quote_url']].index[0]
            if source!=i:
                if source not in links.keys():
                    links[source]=[i]
                elif i not in links[source]:
                    links[source].append(i)
    if currow['urls']!='[]':
        urls=ast.literal_eval(currow['urls'].lower())
        if sum(t_link.isin(urls))>=1:
            source=t_link[t_link.isin(urls)].index[0]
            if source not in links.keys():
                links[source]=[i]
            elif i not in links[source]:
                links[source].append(i)
del currow, source, i, urls
#%%
# Single out the links with at 
links_single=dict()
links_multi=dict()
for i in links.keys():
    if len(links[i])>1:
        links_multi[i]=links[i]
    else:
        links_single[i]=links[i]
del i
#%%
# Make Edges
Edges=[]
size_d=dict()
for i in sorted(links_multi.keys()):
    size_d[i]=len(links_multi[i])
    for j in links_multi[i]:
        Edges.append((i,j))
del i, j
#%% 
N=len(Edges)
#%%
print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
print('bottle neck...')
print('Number of Edges:', N)
t1=dt.now()
print('Time started:', t1)
G=jg.generate(Edges[:N], iterations=500)
t2=dt.now()
diff=t2-t1
print('Time ended:', t2)
print('Elapsed:', diff)
del t1, t2, diff
#%%
# Read in json
#with open(os.path.join(APP_PATH,'data','Twitter','G21434.json'), 'r') as fp:
#    G=json.load(fp)
#G['nodes']={int(k): v for k,v in G['nodes'].items()}
#%%
G_nodes=G['nodes']
G_edges=G['edges']
#%%
labels=[]
node_sizes=[]
groups=[]
for key in G_nodes.keys():
    text=labels_d[key].lower()
    if ("nigeria" in text) or ("pastor chris" in text)  or ("oyakhilome" in text) or ("dino melaye" in text):
        groups.append(0.25)
    elif ("vodafone" in text):
        groups.append(0.5)
    elif ("birmingham" in text) or ("london" in text) or ("leytonstone" in text) or ("merseyside" in text) or (" uk" in text) or ("david icke" in text):
        groups.append(1)
    else:
        groups.append(0)
    if key in size_d.keys():
        node_sizes.append((math.log10(size_d[key]+1))*15)
        labels.append(labels_d[key]+'<br>'+'Connections:'+str(size_d[key]))
    else:
        node_sizes.append(2)
        labels.append(labels_d[key])
del key
#%%
Xn=[G_nodes[k]['location'][0] for k in G_nodes.keys()]# x-coordinates of nodes
Yn=[G_nodes[k]['location'][1] for k in G_nodes.keys()]# y-coordinates
Zn=[G_nodes[k]['location'][2] for k in G_nodes.keys()]# z-coordinates
Xe=[]
Ye=[]
Ze=[]
for e in Edges[:N]:
    Xe+=[G_nodes[e[0]]['location'][0],G_nodes[e[1]]['location'][0], None]
    Ye+=[G_nodes[e[0]]['location'][1],G_nodes[e[1]]['location'][1], None]
    Ze+=[G_nodes[e[0]]['location'][2],G_nodes[e[1]]['location'][2], None]
#%%
trace1=go.Scatter3d(x=Xe,
               y=Ye,
               z=Ze,
               mode='lines',
               line=dict(color='rgb(125,125,125)', width=1),
               hoverinfo='none'
               )

trace2=go.Scatter3d(x=Xn,
               y=Yn,
               z=Zn,
               mode='markers',
               name='actors',
               marker=dict(symbol='circle',
                             size=node_sizes,
                             #color="#e7ad52",
                             color=groups,
                             #colorscale='Viridis',
                             colorscale=[
                                [0, '#E7AD52'],
                                [0.25, plotlycl[0]],
                                [0.5, plotlycl[1]],
                                [0.75, plotlycl[2]],
                                [1, plotlycl[3]],
                                ],
                             line=dict(color='rgb(50,50,50)', width=0.5)
                             ),
               text=labels,
               hoverinfo='text',
               hoverlabel = dict(
                   bgcolor = bgcl,
                   bordercolor=grcl3[1],
                   font=dict(
                       color=grcl3[1]
                   ),
               )
            )

axis=dict(showbackground=False,
          showline=False,
          zeroline=False,
          showgrid=False,
          showticklabels=False,
          title=''
          )

layout = go.Layout(
    title =  dict(
        text ='Network of Twitter accounts with 5G/Coronavirus tweets',
        font =dict(family=plotfont,
                   size=14,
                   color = fontcl
                   ),
                ),
#    width=1000,
#    height=1000,
    showlegend=False,
    scene=dict(
        xaxis=dict(axis),
        yaxis=dict(axis),
        zaxis=dict(axis),
    ),
    paper_bgcolor=bgcl,
    plot_bgcolor=bgcl,
    hovermode='closest',
)

fig=go.Figure(data=[trace1, trace2], layout=layout)
fig.show()    
#fig.write_html("C:/Users/liuz2/Documents/Projects/wuhancv/JSM2020/plots/twitter_21434.html")


# %%
t3=dt.now()
diff=t3-t0
print('-------------------Finish Running Code------------------')
print('Time: ', t3)
print('Time used to run the entire script: ', diff)
del t0, t3, diff
#%%
# Save G as a json file
G_edges2=[]
G_nodes2=dict()
for i in G_edges:
    s=i['source']
    t=i['target']
    G_edges2.append(
        dict(
            source=int(s), 
            target=int(t))
        )
for i in G_nodes.keys():
    G_nodes2[int(i)]=G_nodes[i]
G2=dict()
G2['edges']=G_edges2
G2['nodes']=G_nodes2
with open(os.path.join(APP_PATH,'data','Twitter','G21434.json'), 'w') as fp:
    json.dump(G2, fp)
del i, s, t, G_edges2, G_nodes2, G2
# %%
