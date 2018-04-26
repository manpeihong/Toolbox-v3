# -*- coding: utf-8 -*-
#
# Licensed under the terms of the MIT License
# Copyright (c) 2015 Pierre Raybaut

"""
Simple example illustrating Qt Charts capabilities to plot curves with 
a high number of points, using OpenGL accelerated series
"""

from PyQt5.QtChart import QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis
from PyQt5.QtGui import QPolygonF, QPainter, QBrush, QGradient, QLinearGradient, QColor, QFont, QPen
from PyQt5.QtCore import Qt, QDateTime, QDate, QTime, QPointF
from PyQt5.QtWidgets import QMainWindow

import numpy as np


class Graph(QChartView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)

		self.setpoint_temperature = None

		self.chart = QChart()
		self.chart.legend().hide()
		self.setChart( self.chart )
		self.setRenderHint(QPainter.Antialiasing)
		self.chart.setPlotAreaBackgroundBrush( QBrush(Qt.black) )
		self.chart.setPlotAreaBackgroundVisible( True )

		self.setpointTemperatureSeries = QLineSeries( self.chart )
		pen = self.setpointTemperatureSeries.pen()
		pen.setWidthF(2.)
		pen.setColor( Qt.green )
		self.setpointTemperatureSeries.setPen( pen )
		#self.setpointTemperatureSeries.setUseOpenGL( True )
		self.chart.addSeries( self.setpointTemperatureSeries )

		self.temperatureSeries = QLineSeries( self.chart )
		pen = self.temperatureSeries.pen()
		pen.setWidthF(2.)
		pen.setColor( Qt.red )
		self.temperatureSeries.setPen( pen )
		#self.temperatureSeries.setUseOpenGL( True )
		self.chart.addSeries( self.temperatureSeries )

		self.number_of_samples_to_keep = 2 * 5 * 60

		self.xMin = QDateTime.currentDateTime().toMSecsSinceEpoch()
		self.xMax = QDateTime.currentDateTime().toMSecsSinceEpoch()
		self.yMin = 400
		self.yMax = 0

		#self.chart.createDefaultAxes()
		#x_axis = QValueAxis()
		x_axis = QDateTimeAxis()
		x_axis.setTitleText( "Time" )
		x_axis.setFormat("HH:mm:ss")
		self.chart.addAxis( x_axis, Qt.AlignBottom )
		self.temperatureSeries.attachAxis( x_axis )
		self.setpointTemperatureSeries.attachAxis( x_axis )
		startDate = QDateTime.currentDateTime().addSecs( -5 * 60 )
		endDate = QDateTime.currentDateTime().addSecs( 5 * 60 )
		#startDate = QDateTime(QDate(2017, 1, 9), QTime(17, 25, 0))
		#endDate = QDateTime(QDate(2017, 1, 9), QTime(17, 50, 0))
		#self.chart.axisX().setRange( startDate, endDate )
		#self.chart.axisX().setRange( 0, 100 )

		y_axis = QValueAxis()
		y_axis.setTitleText( "Temperature (K)" )
		self.chart.addAxis( y_axis, Qt.AlignLeft )
		self.temperatureSeries.attachAxis( y_axis )
		self.setpointTemperatureSeries.attachAxis( y_axis )
		self.chart.axisY().setRange( 0, 400 )
		#self.chart.axisY().setRange( 260., 290. )

		self.temperatureSeries.pointAdded.connect( self.Rescale_Axes )
		#self.setpointTemperatureSeries.pointAdded.connect( self.Rescale_Axes )

		self.setRubberBand( QChartView.HorizontalRubberBand )

		# Customize chart title
		font = QFont()
		font.setPixelSize(24);
		self.chart.setTitleFont(font);
		self.chart.setTitleBrush(QBrush(Qt.white));

		## Customize chart background
		#backgroundGradient = QLinearGradient()
		#backgroundGradient.setStart(QPointF(0, 0));
		#backgroundGradient.setFinalStop(QPointF(0, 1));
		#backgroundGradient.setColorAt(0.0, QColor(0x000147));
		#backgroundGradient.setColorAt(1.0, QColor(0x000117));
		#backgroundGradient.setCoordinateMode(QGradient.ObjectBoundingMode);
		#self.chart.setBackgroundBrush(backgroundGradient);
		transparent_background = QBrush(QColor(0,0,0,0))
		self.chart.setBackgroundBrush( transparent_background )

		# Customize axis label font
		labelsFont = QFont()
		labelsFont.setPixelSize(16);
		x_axis.setLabelsFont(labelsFont)
		y_axis.setLabelsFont(labelsFont)
		x_axis.setTitleFont(labelsFont)
		y_axis.setTitleFont(labelsFont)

		# Customize axis colors
		axisPen = QPen(QColor(0xd18952))
		axisPen.setWidth(2)
		x_axis.setLinePen(axisPen)
		y_axis.setLinePen(axisPen)

		# Customize axis label colors
		axisBrush = QBrush(Qt.white)
		x_axis.setLabelsBrush(axisBrush)
		y_axis.setLabelsBrush(axisBrush)
		x_axis.setTitleBrush(axisBrush)
		y_axis.setTitleBrush(axisBrush)

	def set_title(self, title):
		self.chart.setTitle(title)

	def add_new_data_point( self, x, y ):
		x_as_millisecs = x.toMSecsSinceEpoch()
		self.temperatureSeries.append( x_as_millisecs, y )
		if( self.setpoint_temperature ):
			self.setpointTemperatureSeries.append( x_as_millisecs, self.setpoint_temperature )

		num_of_datapoints = self.temperatureSeries.count()
		#if( num_of_datapoints > self.number_of_samples_to_keep ):
		#	self.number_of_samples_to_keep.
		#print( x_as_millisecs, y )
		#self.chart.scroll( x_as_millisecs - 5 * 60 * 1000, x_as_millisecs )
		#self.temperatureSeries.append( x, float(y) )
		#self.repaint()

	def Rescale_Axes( self, index ):
		x = self.temperatureSeries.at( index ).x()
		x_rescaled = False
		if( x < self.xMin ):
			self.xMin = x
			x_rescaled = True
		if( x > self.xMax ):
			self.xMax = x
			x_rescaled = True
		if( x_rescaled ):
			full_range = min( self.xMax - self.xMin, 5 * 60 * 1000 )
			margin = full_range * 0.05

			self.chart.axisX().setRange( QDateTime.fromMSecsSinceEpoch(self.xMax - full_range - margin), QDateTime.fromMSecsSinceEpoch(self.xMax + margin) )
			
		y = self.temperatureSeries.at( index ).y()
		y_rescaled = False
		if( y < self.yMin ):
			self.yMin = y
			y_rescaled = True
		if( y > self.yMax ):
			self.yMax = y
			y_rescaled = True
		if( y_rescaled ):
			full_range = self.yMax - self.yMin
			margin = full_range * 0.05
			self.chart.axisY().setRange( self.yMin - margin, self.yMax + margin )
			