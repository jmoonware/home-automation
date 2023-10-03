import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import numpy as np
import pandas as pd
import viewclasses as vc
import data # the data 'model' 
import view # the 'layout' in dash
import json
import plotly.graph_objects as go
import numpy as np
from datetime import date
from datetime import datetime as dt
import pytz
import numpy as np
import requests

def SetupCallbacks(app):
	""" params: dash app) """

	@app.callback(
		[
			Output(component_id=vc.theYColumnPicker.id,component_property=vc.theYColumnPicker.options),
			Output(component_id='wind_vmph-1m',component_property='children'),
			Output(component_id='wind_vmph-max',component_property='children'),
			Output(component_id='wind_vmph-max-time',component_property='children'),
			Output(component_id='wind_vmph-record',component_property='children'),
			Output(component_id='wind_vmph-record-time',component_property='children'),
			Output(component_id='wind_angle-1m',component_property='children'),
			Output(component_id='wind_angle-24',component_property='children'),
		],
		Input(component_id=vc.theStatsInterval.id, component_property=vc.theStatsInterval.n_intervals)
	)
	def update_wind_gauge_stats(*args):
		
		# VMPH Stats

		# last minute
		vmph_1m='N/A'
		t,r = data.theDataReader.GetCacheData('wind_vmph',oldest_hour=1./60)
		if len(r) > 0:
			vmph_1m="{0:.1f}".format(np.mean(r))

		# last 24 hrs
		vmph_max='N/A'
		nicedt_vmph_max='N/A'
		t,s = data.theDataReader.GetCacheStats('wind_vmph',oldest_hour=24)
		if len(s) > 0 and len(s['max']) > 0:
			max_idx=np.argmax(s['max'])
			vmph_tmax=s['maxtime'][max_idx]
			nicedt_vmph_max='  '+'-'.join(dt.utcfromtimestamp(vmph_tmax).replace(tzinfo=pytz.UTC).astimezone(tz=pytz.timezone('US/Pacific')).isoformat(' ','minutes').split('-')[1:3])
			vmph_max="{0:.1f}".format(np.mean(s['max']))

		
		# all-time record (10 years)
		vmph_max_record='N/A'
		nicedt_vmph_record='N/A'
		t,s = data.theDataReader.GetCacheStats('wind_vmph',oldest_hour=24*3650,hourly=False)
		if len(s) > 0 and len(s['max']) > 0:
			max_idx=np.argmax(s['max'])
			vmph_tmax=s['maxtime'][max_idx]
			nicedt_vmph_record='  '+'-'.join(dt.utcfromtimestamp(vmph_tmax).replace(tzinfo=pytz.UTC).astimezone(tz=pytz.timezone('US/Pacific')).isoformat(' ','minutes').split('-')[0:3])
			vmph_max_record="{0:.1f}".format(np.max(s['max']))
			
		# wind angle
		
		sector_text=['N','NE','E','SE','S','SW','W','NW','N']
		sector_start=np.array([0,45,90,135,180,225,270,315,360])
		
		dir_med_1m='N/A'
		t,r = data.theDataReader.GetCacheData('wind_angle',oldest_hour=1./60)
		if len(r) > 0:	
			deg_med_1m=np.mean(r)
			dir_med_1m='{0} ({1:.1f})'.format(sector_text[np.argmin(abs(sector_start-deg_med_1m))],deg_med_1m)

		t,s = data.theDataReader.GetCacheStats('wind_angle',oldest_hour=24)
		dir_med_24='N/A'
		if len(s) > 0 and len(s['p50']) > 0:
			deg_med_24=np.median(s['p50'])
			dir_med_24='{0} ({1:.1f})'.format(sector_text[np.argmin(abs(sector_start-deg_med_24))],deg_med_24)


		# update logged data origins
		options=[{'label':v,'value':v} for v in data.theDataReader.data_cache.keys()]


		return options, vmph_1m,vmph_max,nicedt_vmph_max,vmph_max_record,nicedt_vmph_record,dir_med_1m,dir_med_24

	@app.callback(
		[
			Output(component_id='forecast', component_property='children'),
			Output(component_id='forecast-1', component_property='children'),
		],
		Input(component_id=vc.theForecastInterval.id, component_property=vc.theForecastInterval.n_intervals)
	)
	def update_forecast(*args):
		forecast_string = 'None'
		forecast_string_1 = 'None'
		
		# Get the forecast string from National Weather Service
		forecast_url = r'https://forecast.weather.gov/MapClick.php?lon=-117.16695785522462&lat=33.04002531855252'
		r = None
		forecast_strings = []
		try:
			with requests.Session() as req:
				r = req.get(forecast_url)
			if r:
				lines=r.text.split('\n')
				for l,nl in zip(lines[:-1],lines[1:]):
					if 'period-name' in l:
						forecast_strings.append(nl.split('title=')[1].split('class')[0])
		except Exception as ex:
			pass

		if len(forecast_strings) > 1:
			forecast_string = forecast_strings[0]
			forecast_string_1 = forecast_strings[1]

		return forecast_string, forecast_string_1





	@app.callback(
		[
			Output(component_id='temp-now', component_property='children'),
			Output(component_id='temp-max-24', component_property='children'),
			Output(component_id='temp-min-24', component_property='children'),
			Output(component_id='humidity-now', component_property='children'),
			Output(component_id='humidity-max-24', component_property='children'),
			Output(component_id='humidity-min-24', component_property='children'),
			Output(component_id='precip-1hr', component_property='children'),
			Output(component_id='precip-24hr', component_property='children'),
			Output(component_id='precip-ytd', component_property='children'),
		],
		Input(component_id=vc.theInterval.id, component_property=vc.theInterval.n_intervals)
	)
	def update_gauges(*args):
		
		current_temp = "{0:.1f}".format(np.random.rand()*60)
		current_humidity = "{0:.1f}".format(np.random.rand()*100)
		precip_1hr = "{0:.1f}".format(np.random.rand()*10)

		newvals=data.theDataReader.GetLatestReadings()
		if 'outside_T' in newvals:
			current_temp="{0:.1f}".format((9*newvals['outside_T']['reading']/5.)+32)

		if 'outside_H' in newvals:
			current_humidity="{0:.1f}".format(newvals['outside_H']['reading'])

		if 'precip_inphr' in newvals:
			precip_1hr="{0:.1f}".format(newvals['precip_inphr']['reading'])

		# last 24 hrs
		max_temp='N/A'
		min_temp='N/A'
		t,s = data.theDataReader.GetCacheStats('outside_T',oldest_hour=24)
		if len(s) > 0 and len(s['max']) > 0:
			max_temp="{0:.1f}".format(9*np.max(s['max'])/5. + 32)
		if len(s) > 0 and len(s['min']) > 0:
			min_temp="{0:.1f}".format(9*np.min(s['min'])/5. + 32)

		# last 24 hrs
		max_humidity='N/A'
		min_humidity='N/A'
		t,s = data.theDataReader.GetCacheStats('outside_H',oldest_hour=24)
		if len(s) > 0 and len(s['max']) > 0:
			max_humidity="{0:.1f}".format(np.max(s['max']))
		if len(s) > 0 and len(s['min']) > 0:
			min_humidity="{0:.1f}".format(np.min(s['min']))


		precip_24hr = 'N/A'
		t,readings = data.theDataReader.GetCacheData('precip_inphr',oldest_hour=24)
		if len(readings) > 0:
			precip_24hr = "{0:.1f}".format(np.sum(readings))
		precip_ytd = 'N/A'

	

		return current_temp, max_temp, min_temp, current_humidity, max_humidity, min_humidity, precip_1hr, precip_24hr, precip_ytd

	@app.callback(
		[
			Output(component_id=vc.theSpeedGauge.id, component_property=vc.theSpeedGauge.figure),
			Output(component_id=vc.theAngleGauge.id, component_property=vc.theAngleGauge.figure),
#			Output(component_id='wind_vmph-lastupdate',component_property='children'),
			Output(component_id='wind_angle-lastupdate',component_property='children'),
			Output(component_id='wind_angle-lastupdate',component_property='className'),
		],
		Input(component_id=vc.theInterval.id, component_property=vc.theInterval.n_intervals)
	)
	def update_wind_gauge(*args):
		
		vmph=np.random.rand()*60
		deg = 360*np.random.rand()
#		vmph_lastupdate='N/A'
		dir_lastupdate='N/A'
		text_lastupdate='text-warning'
	
		newvals=data.theDataReader.GetLatestReadings()
		if 'wind_vmph' in newvals:
			vmph=newvals['wind_vmph']['reading']
			# nothing is simple
#			vmph_lastupdate='-'.join(dt.utcfromtimestamp(newvals['wind_vmph']['time']).replace(tzinfo=pytz.UTC).astimezone(tz=pytz.timezone('US/Pacific')).isoformat(' ','minutes').split('-')[0:3])

		
		if 'wind_angle' in newvals:
			deg = newvals['wind_angle']['reading']
			last_dt=dt.utcfromtimestamp(newvals['wind_angle']['time']).replace(tzinfo=pytz.UTC)
			dir_lastupdate='-'.join(last_dt.astimezone(tz=pytz.timezone('US/Pacific')).isoformat(' ','seconds').split('-')[0:3])
			now=dt.now(pytz.utc).replace(tzinfo=pytz.UTC)
			if (now-last_dt).total_seconds() < 120:
				text_lastupdate='text-success'
			

		speed_deg=vmph*270./60.
		
		# use polar plot as wind direction indicator with hand-drawn arrow
		fig_speed = go.Figure(
			go.Scatterpolar(
				r=[0,0.95],
				theta=[speed_deg,speed_deg],
				mode="lines", 
				line_color="rgba(255,100,100,255)",
				line_width=4,
			)
		)
		
		fig_speed.add_trace(
			go.Scatterpolar(
				r=[0.7],
				theta=[-45],
				text=["{0:.1f}".format(vmph)],
				mode="text", 
				textfont=dict(
					size=45,
					color='rgba(210,230,255,255)'
				)
			)
		)
		fig_speed.add_trace( # little circle in center
			go.Scatterpolar(
				r=[0.0],
				theta=[0],
				text=['\u2299'],
				mode="text", 
				textposition='middle center',
				textfont=dict(
					family='Times',
					size=20,
					color='rgba(210,230,255,255)'
				)
			)
		)
		
		h_w=375
		m_d=40
		
		fig_speed.update_layout(
			showlegend=False,
			autosize=True,
			template='plotly_dark',
			plot_bgcolor='rgba(0, 0, 0, 0)',
			paper_bgcolor='rgba(0, 0, 0, 0)',
#			height=h_w,
#			width=h_w,
			margin=dict(
				l=m_d,
				r=m_d,
				b=m_d,
				t=m_d
			),
#			title={'text':'Wind Direction','font':{'size':30}},
			polar = dict(
				radialaxis = dict(range=[0, 1], showticklabels=False, ticks='',showgrid=False),
				angularaxis = dict(showticklabels=True, ticks='inside',tickmode='array',tickvals=[0,22.5,45,90,135,180,225,270],ticktext=["0","","10","20","30","40","50","60"],tickfont={'size':20},rotation=225,direction='clockwise',showgrid=False,tickwidth=4)
			)
		)

		sector_text=['N','NE','E','SE','S','SW','W','NW','N']
		sector_start=np.array([0,45,90,135,180,225,270,315,360])
		dir_text=sector_text[np.argmin(abs(sector_start-deg))]
		
		# use polar plot as wind direction indicator with hand-drawn arrow
		fig_angle = go.Figure(
			go.Scatterpolar(
				r=[0.95,0,0.25,0,0.25,0],
				theta=[deg,0,deg-30,0,deg+30,0],
				mode="lines", 
				line_color="rgba(255,100,100,255)",
				line_width=4
			))
		fig_angle.add_trace(
			go.Scatterpolar(
				r=[0.7],
				theta=[180],
				text=[dir_text],
				mode="text", 
				textfont=dict(
					size=45,
					color='rgba(210,230,255,255)'
				)
			)
		)
		fig_angle.update_layout(
			showlegend=False,
			autosize=True,
			template='plotly_dark',
			plot_bgcolor='rgba(0, 0, 0, 0)',
			paper_bgcolor='rgba(0, 0, 0, 0)',
#			height=h_w,
#			width=h_w,
			margin=dict(
				l=m_d,
				r=m_d,
				b=m_d,
				t=m_d
			),
#			title={'text':'Wind Direction','font':{'size':30}},
			polar = dict(
				radialaxis = dict(range=[0, 1], showticklabels=False, ticks='',showgrid=False),
				angularaxis = dict(showticklabels=True, tickmode='array',tickvals=[0,45,90,135,180,225,270,315],ticktext=['N','NE','E','SE','S','SW','W','NW'],tickfont={'size':20},rotation=90,direction='clockwise',tickwidth=4),
			)
		)
		
		
		# update the stats panels
		
		return fig_speed, fig_angle, dir_lastupdate, text_lastupdate

	@app.callback(
		Output(component_id=vc.theDataGraph.id, component_property=vc.theDataGraph.figure),
		[
#		Input(component_id=vc.theLocalGranularityState.id, component_property=vc.theLocalGranularityState.value),
#		Input(component_id=vc.theLocalTimeSpanState.id, component_property=vc.theLocalTimeSpanState.value),
		Input(component_id='radio-plot-grain', component_property='value'),
		Input(component_id='radio-plot-span', component_property='value'),
		Input(component_id=vc.theYColumnPicker.id,component_property=vc.theYColumnPicker.value),		
		Input(component_id='plot-date-picker',component_property='date'),
		]
	)
	def update_data_graph(*args):
	
		granularity=args[0]
		timespan=args[1]
		
		now=date.today()
		
		print((granularity, timespan))
		
		ycol='wind_vmph'		
		if len(args) > 1:
			ycols=args[2]
		
		if len(args) > 2:
			start_date=args[3]
		
#		print(start_date)
		naive_start_dt=dt.strptime(start_date,"%Y-%m-%d")
		print(naive_start_dt)

		if naive_start_dt.date() < now: # if it is today just let DataReader calculate now
			local_time = pytz.timezone("US/Pacific")
			local_datetime = local_time.localize(naive_start_dt, is_dst=None)
			utc_start_datetime = local_datetime.astimezone(pytz.utc)
		else:
			utc_start_datetime=None
			
		print(utc_start_datetime)
	
		if ycols==None:
			fig = {}
			
		hours=timespan

		
		the_plots=[]
		the_stats=[]
		the_labels=[]
		print(granularity,hours)
		
		for ycol in ycols:
			times=[]
			readings=[]
			if granularity=='points':
				times,readings = data.theDataReader.GetCacheData(ycol,oldest_hour=hours) # TODO - Add drop down, time boxes
			elif granularity=='hourly':
				# start_time_utc=None,newest_hour=0,oldest_hour=24,hourly=True
				times,rd = data.theDataReader.GetCacheStats(ycol,start_time_utc=utc_start_datetime,oldest_hour=hours,hourly=True)
				if 'p50' in rd:
					readings = rd['p50']
				the_stats.append({'x':times,'y':rd})
			elif granularity=='daily':
				# start_time_utc=None,newest_hour=0,oldest_hour=24,hourly=True
				times,rd = data.theDataReader.GetCacheStats(ycol,start_time_utc=utc_start_datetime,oldest_hour=hours,hourly=False)
				if 'p50' in rd:
					readings = rd['p50']
				the_stats.append({'x':times,'y':rd})
			the_plots.append({'x':times,'y':readings})
			the_labels.append(ycol)

	
		fig = go.Figure()

		if granularity=='points':
			for d,l in zip(the_plots,the_labels):
				fig.add_trace(go.Scatter(x=d['x'],y=convert_points(d['y'],l),mode='lines',name=l))
		else:
			# add empty traces
			for s,n in zip(the_stats,the_labels):
				s['y']=convert_stats(s['y'],n)
				fig.add_trace(go.Box(y=[[v] for v in s['y']['p50']],x=s['x'],boxpoints=False,name=n))
				# now update pre-computed quartiles
				fig.update_traces(q1=s['y']['p25'], median=s['y']['p50'],
								  q3=s['y']['p75'], lowerfence=s['y']['min'],
								  upperfence=s['y']['max'], mean=s['y']['mean'],
								  sd=s['y']['std'],selector=dict(name=n))
			
		fig.update_layout(
			template='plotly_dark',
			xaxis={'fixedrange':True},
			yaxis={'fixedrange':True},
			margin=dict(
				l=30,
				r=30,
				b=30,
				t=30
			),
			legend=dict(
				yanchor="top",
				y=0.99,
				xanchor="left",
				x=0.01
			),
		)
		
		return fig
		
		
	@app.callback(
		Output("collapse", "is_open"),
		[Input("collapse-button", "n_clicks")],
		[State("collapse", "is_open")],
	)
	def toggle_collapse(n, is_open):
		print('gah '+str(n))
		if n:
			return not is_open
		return is_open
		
	def convert_stats(s,label):
		keys=['min','max','p25','p50','p75','mean','std'] # keys to convert
		for k in keys:
			if k in s:
				if "_T" in label: # convention for temperatures in C
					if k=='std': # KLUDGE for stdev values
						offset=0
					else:
						offset=32
					s[k]=[(9.*v/5.)+offset for v in s[k]] # convert to F
			else:
				s[k]=[]
		return s
					
	def convert_points(d,label):
		if "_T" in label: # convention for temperatures in C
			return((9.*d/5.)+32) # convert to F
		else:
			return(d)