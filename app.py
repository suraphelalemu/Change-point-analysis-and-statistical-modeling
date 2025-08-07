import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import os

# Initialize the Dash app
app = dash.Dash(__name__, title="Oil Price Analysis Dashboard")

# Load data
df = pd.read_csv('data/processed/cleaned_oil_prices.csv', parse_dates=['Date'])
change_points = pd.read_csv('outputs/change_point_impacts.csv', parse_dates=['start_date', 'end_date'])
events = pd.read_csv('data/processed/events_annotated.csv', parse_dates=['Date'])
event_correlations = pd.read_csv('outputs/event_correlations.csv', parse_dates=['change_point_date', 'event_date'])

app.layout = html.Div([
    html.H1("Brent Oil Price Change Point Analysis"),
    
    dcc.Tabs([
        dcc.Tab(label='Price Trend', children=[
            dcc.Graph(id='price-chart'),
            html.Div([
                dcc.RangeSlider(
                    id='date-slider',
                    min=df['Date'].min().timestamp(),
                    max=df['Date'].max().timestamp(),
                    value=[df['Date'].min().timestamp(), df['Date'].max().timestamp()],
                    marks={int(pd.Timestamp(year).timestamp()): str(year) 
                           for year in range(1987, 2023, 5)}
                )
            ], style={'margin': '20px'})
        ]),
        
        dcc.Tab(label='Change Points', children=[
            html.Div([
                html.H3("Detected Structural Breaks"),
                dcc.Graph(id='change-point-chart'),
                html.H4("Regime Statistics:"),
                dash.dash_table.DataTable(
                    id='regime-table',
                    columns=[{"name": i, "id": i} for i in change_points.columns],
                    data=change_points.to_dict('records'),
                    style_table={'overflowX': 'auto'}
                )
            ])
        ]),
        
        dcc.Tab(label='Event Correlation', children=[
            html.Div([
                html.H3("Change Points Correlated with Events"),
                dash.dash_table.DataTable(
                    id='event-table',
                    columns=[{"name": i, "id": i} for i in event_correlations.columns],
                    data=event_correlations.to_dict('records'),
                    style_table={'overflowX': 'auto'}
                ),
                html.H4("All Recorded Events:"),
                dash.dash_table.DataTable(
                    id='all-events-table',
                    columns=[{"name": i, "id": i} for i in events.columns],
                    data=events.to_dict('records'),
                    style_table={'overflowX': 'auto'}
                )
            ])
        ])
    ])
])

@app.callback(
    Output('price-chart', 'figure'),
    [Input('date-slider', 'value')]
)
def update_price_chart(date_range):
    start_date = pd.to_datetime(date_range[0], unit='s')
    end_date = pd.to_datetime(date_range[1], unit='s')
    
    filtered_df = df[(df['Date'] >= start_date) & (df['Date'] <= end_date)]
    
    fig = px.line(filtered_df, x='Date', y='Price', 
                 title='Brent Crude Oil Prices Over Time')
    
    # Add change points
    for _, cp in change_points.iterrows():
        if start_date <= cp['start_date'] <= end_date:
            fig.add_vline(x=cp['start_date'], line_dash="dash", line_color="red")
    
    # Add events
    for _, event in events.iterrows():
        if start_date <= event['Date'] <= end_date:
            fig.add_vline(x=event['Date'], line_dash="dot", line_color="green")
    
    return fig

@app.callback(
    Output('change-point-chart', 'figure'),
    [Input('date-slider', 'value')]
)
def update_change_point_chart(date_range):
    start_date = pd.to_datetime(date_range[0], unit='s')
    end_date = pd.to_datetime(date_range[1], unit='s')
    
    filtered_cp = change_points[
        (change_points['start_date'] >= start_date) & 
        (change_points['end_date'] <= end_date)
    ]
    
    fig = px.bar(filtered_cp, x='start_date', y='mean_price',
                color='volatility',
                title='Mean Price by Regime',
                labels={'mean_price': 'Mean Price (USD)', 'start_date': 'Regime Start Date'})
    
    return fig

if __name__ == '__main__':
    app.run(debug=True)