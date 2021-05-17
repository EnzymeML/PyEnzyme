# First Try Visualisation with Dash
import dash
import dash_core_components as dcc
import plotly.express as px
import plotly.graph_objs as go
import dash_html_components as html
from dash.dependencies import Input, Output, State
#Save Data in a dictionary
s1 = {'x': (0,1,2,3,4,5,6,7,8,9),
     'y1':(0.25,0.65,0.37,0.40,0.76,0.95,0.77,0.83,0.91,2.00),
     'y2':(0.54,0.84,0.94,1.20,2.40,2.50,3.00,3.24,3.50,4.00),
     'y3':(0.42,0.72,0.33,0.12,0.53,0.63,0.67,0.28,0.19,6.00)}
s2 = {'x': (0,1,2,3,4,5,6,7,8,9),
     'y1':(0.5,0.6,0.7,0.4,0.7,0.9,0.7,0.3,0.1,1.0),
     'y2':(0.4,0.8,0.4,1.20,1.40,1.50,2.00,1.24,2.50,1.20),
     'y3':(0.2,0.7,0.3,0.12,0.3,0.6,0.7,0.8,0.19,1.00)}
s3 = {'x': (0,1,2,3,4,5,6,7,8,9),
     'y1':(0.15,0.78,0.26,0.45,0.23,0.48,0.79,0.26,0.46,1.5),
     'y2':(0.34,0.64,0.49,1.00,1.92,1.47,0.86,1.52,1.00,1.30),
     'y3':(2.00,1.76,1.56,1.35,1.44,1.69,1.33,1.26,0.99,0.56)}
     #visualisation using dash

app = dash.Dash(__name__)

colors = {
    'background': '#fffff',
    'text': '#0a0a0d'
}
options=[
            {'label': 'substrate_1', 'value': 's_1'},
            {'label': 'substrate_2', 'value': 's_2'},
            {'label': 'substrate_3', 'value': 's_3'}
]
all_substrates = [option["value"] for option in options]
app.layout = html.Div([
# hedline
    html.H1(
        children='Visualization example',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
),
#subheading
    html.Div(children='exmaple nr.1', style={
        'textAlign': 'center',
        'color': colors['text']
        }
),
#checkliste in dsa Layout mit rein
dcc.Checklist(
            id="all-checklist",
            options=[{"label": "All", "value": "All"}],
            values=[],
            labelStyle={"display": "inline-block"},
),
#Mit dcc.chechlist wird eine Liste eingefügt bei der
# der user die substrate auswählen kann
    dcc.Checklist(
        id='checklist',
        options= options,
        values=[],
        labelStyle={'display': 'inline-block'}
 ),
#unterhalb der checklists wird eine line erstellt
#mit einem markdown der die infos der reactionsbedingungen enthält
#von https://dash.plotly.com/clientside-callbacks
  html.Hr(),
        html.Details([
            html.Summary('reaction condition'),
            dcc.Markdown(
                id='reac_con'
                ),
            html.Details([
                html.Summary('temperature'),
                dcc.Markdown(
                    id='T'
                )
            ]),
            html.Details([
                html.Summary('pH-value'),
                dcc.Markdown(
                    id='pH'
                )
             ]),
            html.Details([
                html.Summary('reactant names'),
                dcc.Markdown(
                    id='react_n'
                )
            ]),
        ]),
#hier @app.callback einfügen um, daten der verschiedenen
#Substrate in die checklist einzufügen
# schau hier : https://dash.plotly.com/basic-callbacks
#main graph 
    dcc.Graph(
        id='Graph1',
        figure={
            'data': [
            #soll unter checklist substrate_1 gespeichert werden
                {'x': s1['x'], 'y': s1['y1'], 'type': 'scatter', 'name': 'repl_1'},
                {'x': s1['x'], 'y': s1['y2'], 'type': 'scatter', 'name': 'repl_2'},
                {'x': s1['x'], 'y': s1['y3'], 'type': 'scatter', 'name': 'repl_3'},
             #soll unter checklist substrate_2 gespeichert werden   
                {'x': s2['x'], 'y': s2['y2'], 'type': 'scatter', 'name': 'repl_1'},
                {'x': s2['x'], 'y': s2['y3'], 'type': 'scatter', 'name': 'repl_2'},
                {'x': s2['x'], 'y': s2['y2'], 'type': 'scatter', 'name': 'repl_3'},
            #soll unter checklist substrate_3 gespeichert werden
                {'x': s3['x'], 'y': s3['y3'], 'type': 'scatter', 'name': 'repl_1'},
                {'x': s3['x'], 'y': s3['y2'], 'type': 'scatter', 'name': 'repl_2'},
                {'x': s3['x'], 'y': s3['y3'], 'type': 'scatter', 'name': 'repl_3'},
                
            ],
            'layout': {
#change the layout background using the plot_bgcolor
                'plot_bgcolor': colors['background'],
                'paper_bgcolor': colors['background'],
                'font': {
                    'color': colors['text']
                }
            }
        }
    ),
]) 
# Beispiel von http://dash.plotly.com/advanced-callbacks
@app.callback(
    Output("checklist", "values"),
    Output("all-checklist", "values"),
#Input musss noch angepasst werden damit die verbindung von
#all auch mit den anderen checklist steht    
    Input("checklist", "values"),
    Input("all-checklist", "values"),
)
def sync_checklists(substrate_selected, all_selected):
    ctx = dash.callback_context
    input_id = ctx.triggered[0]["prop_id"].split(".")[0]
    if input_id == "checklist":
        all_selected = ["All"] if set(substrate_selected) == set(all_substrates) else []
    else:
        substrate_selected = all_substrates if all_selected else []
    return substrate_selected, all_selected

if __name__=="__main__":
    app.run_server(debug=True)