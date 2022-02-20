
import dash
from dash import dcc
from dash import html
from dash import dash_table
import dash_daq as daq
import dash_bootstrap_components as dbc

from datetime import date

import control
import viewclasses as vc
import json


textcolor='rgba(210,230,255,255)'

def SetupView(controller,dr):
	""" SetupView - sets up view elements

	Arguments:
		controller {Controller Class} -- Controller for program

	"""

	app=controller.app
#	lo=[html.H2(children='Project')]
	lo=[]
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					[
						dcc.Graph(id=vc.theSpeedGauge.id,config={'staticPlot':True}), #,style={'width': '90vw', 'height': '90vh'}),
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H4("Wind Speed (MPH)", className="text-primary"),
										dbc.ListGroup(
											[
												html.H5("Average (1 min):"),
												dbc.ListGroupItem(html.H3("N/A",id='wind_vmph-1m',className='text-primary'),style={'textAlign': 'center'}),
												
												html.H5("Max (24 hrs):"),
												dbc.ListGroupItem(html.H3("N/A",id='wind_vmph-max',className='text-primary'),style={'textAlign': 'center'}),
												dbc.ListGroupItem(html.H5("Now",id='wind_vmph-max-time',className="text-primary"),style={'textAlign': 'center'}),

												html.H5("Record:"),
												dbc.ListGroupItem(html.H3("N/A",id='wind_vmph-record',className='text-primary'),style={'textAlign': 'center'}),
												dbc.ListGroupItem(html.H5("Now",id='wind_vmph-record-time',className="text-primary"),style={'textAlign': 'center'}),
									
											]
										),
									]
								)
							],

						),

					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),
				dbc.Col(
					[
						dcc.Graph(id=vc.theAngleGauge.id,config={'staticPlot':True}), #,style={'width': '90vw', 'height': '90vh'})
						dbc.Card(
							[
								dbc.CardBody(
									[
										html.H4("Wind Angle", className="text-primary"),
										dbc.ListGroup(
											[
												html.H5("Average (1 min):"),
												dbc.ListGroupItem(html.H3("N",id='wind_angle-1m',className="text-primary"),style={'textAlign': 'center'}),

												html.H5("Median (24 hrs):"),
												dbc.ListGroupItem(html.H3("N",id='wind_angle-24',className="text-primary"),style={'textAlign': 'center'}),
											]
										)
									]
								)
							],
						),
						html.Div(' ',style={'margin-bottom': 25}),
						dbc.Card(
							[
								dbc.CardBody(
									[
										dbc.ListGroup(
											[
												
												html.H5("Last Update: "),
												dbc.ListGroupItem(html.H5("Now ",id='wind_angle-lastupdate',className="text-success"),style={'textAlign': 'center'}),
											],
										),
									],
								),
							],
						),	
					],
					xs=11,
					sm=11,
					md=5,
					lg=5,
					xl=5,
				),
			],
			justify='center',
		)
	)

	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Graph(id=vc.theDataGraph.id)
			)
		)
	)
	
	lo.append(
		dbc.Row(
			dbc.Col(
				html.Div(' ',style={'margin-bottom': 25})
			)
		)
	)
	
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					[
						html.H4('From Date:'),
						dcc.DatePickerSingle(
								 id='plot-date-picker',
								 min_date_allowed=date(2022, 2, 9),
#								 max_date_allowed=date(2017, 9, 19),
								 initial_visible_month=date.today(),
								 date=date.today(),
								 className='dark-theme-control'
						)
					],
#					width=4,
				),
				dbc.Col(
					html.Div(
						[
							html.H4('Plot for (days):'),
							dbc.RadioItems(	
								id="radio-plot-span",
								className="btn-group",
								inputClassName="btn-check",
								labelClassName="btn btn-outline-primary btn-lg",
								labelCheckedClassName="active",
								options=[
									{"label": "1", "value": 24},
									{"label": "3", "value": 72},
									{"label": "7", "value": 7*24},
								],
								value=24,
							)
						],
	#					width=4,
						className='radio-group',
					)	
				),
				dbc.Col(
					html.Div(
						[
							html.H4('Plot by:'),
							dbc.RadioItems(	
								id="radio-plot-grain",
								className="btn-group",
								inputClassName="btn-check",
								labelClassName="btn btn-outline-primary btn-lg",
								labelCheckedClassName="active",
								options=[
									{"label": "Hourly", "value": 'hourly'},
									{"label": "Daily", "value": 'daily'},
									{"label": "Points", "value": 'points'},
								],
								value='hourly',
							)
						],
	#					width=4,
						className='radio-group',
					)
				)
			],
#			justify='center',
		)
	)
	
	lo.append(
		dbc.Row(
			dbc.Col(
				html.Div(' ',style={'margin-bottom': 25})
			)
		)
	)
	
	lo.append(
		dbc.Row(
			[
				dbc.Col(
					dbc.Button(
						"Available Data",
						id="collapse-button",
						outline=True,
						class_name='btn btn-outline-primary btn-lg',
						n_clicks=0,
					),
#					width=4,
				),
				dbc.Col(
					dbc.Collapse(
						dcc.Checklist(
							options=[{'label':v,'value':v} for v in dr.data_cache.keys()],
							value=['wind_vmph'],
							inputClassName='form-check-input',
							labelStyle = dict(display='block',className='form-check-label'),
							id=vc.theYColumnPicker.id
						),
						id="collapse",
						is_open=False,
						className='form-check',
					),
#					width=4
				),
			],
#			justify='center'
		)
	)

	
	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Interval(interval=vc.theStatsInterval.interval,id=vc.theStatsInterval.id,n_intervals=0)
			)
		)
	)

	lo.append(
		dbc.Row(
			dbc.Col(
				dcc.Interval(interval=vc.theInterval.interval,id=vc.theInterval.id,n_intervals=0)
			)
		)
	)

	
	
	#	lo.append(html.Div(id=vc.theLocalData.id,children=df.to_json(orient='split'),style={'display': 'none'}))
	lo.append(
		dbc.Row(
			[
				html.Div(id=vc.theLocalGranularityState.id,style={'display': 'none'},children=json.dumps({'granularity':'plot-button-points'})),
				html.Div(id=vc.theLocalTimeSpanState.id,style={'display': 'none'},children=json.dumps({'timespan':'plot-button-24'}))
			]
		)
	)

#	rc=[dbc.Row(lo)]
	
	app.layout=html.Div(children=lo)
