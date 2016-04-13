import sys, os, csv,random
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4.Qwt5 as Qwt
from dmm_monitor import DmmMonitorThread
from PyQt4.Qwt5.anynumpy import *
import random
from PyQt4 import Qt


class PlottingDataMonitor(QMainWindow):
    def __init__(self, parent=None):
        super(PlottingDataMonitor, self).__init__(parent)

        self.monitor_active = False 
        self.dmm_monitor=None
        self.curve=[None]
        self.temperature_samples = []

        self.timer = QTimer()
        self.create_menu()
        self.create_main_frame()
        self.create_status_bar()
        self.create_panner()
        # Activate start-stop button connections
        self.connect(self.button_Connect, SIGNAL("clicked()"),
                    self.OnStart)
        self.connect(self.button_Disconnect, SIGNAL("clicked()"),
                    self.OnStop)

    def save_plot(self):
		file_choices = "PNG (*.png)|*.png"
		path = unicode(QFileDialog.getSaveFileName(self,'Save file', '',file_choices))
		if path:
			i = QtGui.QImage()
			i.save(path)
			# self.canvas.print_figure(path, dpi=self.dpi)
			self.statusBar().showMessage('Saved to %s' % path, 2000)
    	
    def create_action(self,text,slot=None,shortcut=None,icon=None,tip=None,checkable=False,signal="triggered()"):
    	action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action

    def add_actions(self, target, actions):
		for action in actions:
			if action is None:
			    target.addSeparator()
			else:
			    target.addAction(action)

    def create_menu(self):
		self.file_menu = self.menuBar().addMenu("&File")
		#load_file_action = self.create_action("&Save plot",shortcut="Ctrl+S", slot=self.save_plot, tip="Save the plot")
		load_file_action=self.create_action("&Save plot",shortcut="Ctrl+S",slot=self.save_plot,tip="Save the Plot")
		self.add_actions(self.file_menu, (load_file_action,None))

    def create_com_box(self):
		""" 
		Purpose:   create the Start and Stop Reading groupbox
		Return:    return a layout of the Start and Stop Reading Button
		"""
		self.com_box = QGroupBox("Start and Stop Reading")

		com_layout = QGridLayout()

		self.measure_voltage     =    QRadioButton("voltage")
		self.measure_voltage.setChecked(1)
		self.measure_current    =    QRadioButton("current")
		self.measure_resistance    =    QRadioButton("resistance")
		self.button_Connect      =   QPushButton("Start")
		self.button_Disconnect   =   QPushButton("Stop")
		self.button_Disconnect.setEnabled(False)
		
		com_layout.addWidget(self.measure_voltage,0,0)
		com_layout.addWidget(self.measure_current,0,1)
		com_layout.addWidget(self.measure_resistance,0,2)

		com_layout.addWidget(self.button_Connect,1,0)
		com_layout.addWidget(self.button_Disconnect,1,1)        

		return com_layout

    def create_plot(self):
        plot = Qwt.QwtPlot(self)
        plot.setCanvasBackground(Qt.Qt.black)
        # plot.plotLayout().setAlignCanvasToScales(True)
        # plot.insertLegend(Qwt.QwtLegend(), Qwt.QwtPlot.BottomLegend)
        plot.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
        #plot.setAxisScale(Qwt.QwtPlot.xBottom, 0, 10, 1)
        plot.setAxisTitle(Qwt.QwtPlot.yLeft, 'voltage')
        #plot.setAxisScale(Qwt.QwtPlot.yLeft, 0, 30, 5)
        plot.setFixedHeight(400)
        plot.replot()

        self.zoomer = Qwt.QwtPlotZoomer(plot.canvas())
        self.zoomer.setMousePattern(Qwt.QwtEventPattern.MouseSelect2,
                               Qt.Qt.RightButton, Qt.Qt.ControlModifier)
        self.zoomer.setMousePattern(Qwt.QwtEventPattern.MouseSelect3,
                               Qt.Qt.RightButton)
        self.zoomer.setRubberBandPen(Qt.Qt.darkBlue)
        self.zoomer.setTrackerPen(Qt.Qt.darkBlue)
        self.panner = Qwt.QwtPlotPanner( plot.canvas() )
        self.panner.setAxisEnabled(Qwt.QwtPlot.yRight, False)
        self.panner.setAxisEnabled(Qwt.QwtPlot.xBottom, False)

        self.panner.setMouseButton (Qt.Qt.LeftButton)
        curve = [None]*1
        pen = [QPen(QColor('limegreen')) ]
        
        curve[0] =  Qwt.QwtPlotCurve('')
        curve[0].setRenderHint(Qwt.QwtPlotItem.RenderAntialiased)
        pen[0].setWidth(1)
        curve[0].setPen(pen[0])
        curve[0].attach(plot)

        return plot,curve

    def create_status_bar(self):
        self.status_text = QLabel('Monitor idle')
        self.statusBar().addWidget(self.status_text, 1)


    def create_panner(self):
        pass
        # self.panner.setMouseButton(Qt.Qt.MidButton)
        
    def create_main_frame(self):

    	#start and stop reading button
    	portname_layout = self.create_com_box()

    	self.com_box.setLayout(portname_layout)
    	# Plot 
        self.plot,self.curve = self.create_plot()
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plot)
        plot_groupbox = QGroupBox('Plot')
        plot_groupbox.setLayout(plot_layout)
        plot_groupbox.resize(700,700)
        
        # Main frame and layout
        self.main_frame = QWidget()
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.com_box)
        main_layout.addWidget(plot_groupbox)
        main_layout.addStretch(1)
        self.main_frame.setLayout(main_layout)
        
        self.setCentralWidget(self.main_frame)


    
    def OnStart(self):
		self.button_Connect.setEnabled(False)
		self.button_Disconnect.setEnabled(True)
		self.measure_input=''
		self.temperature_samples=[]
		if not self.measure_voltage.isChecked():
			self.measure_voltage.setEnabled(False)
		else:
			self.measure_input="voltage"	

		if not self.measure_current.isChecked():
			self.measure_current.setEnabled(False)
		else:
			self.measure_input="current"	

		if not self.measure_resistance.isChecked():
			self.measure_resistance.setEnabled(False)
		else:
			self.measure_input="resistance"

		self.monitor_active = True
		self.plot.setAxisTitle(Qwt.QwtPlot.yLeft, self.measure_input)
		self.data_q      =  []
		self.error_q     =  []
		self.dmm_monitor =  DmmMonitorThread(self.data_q,self.error_q,self.measure_input)
		print self.dmm_monitor
		dmm_connect_succ=self.dmm_monitor.start()
		print "dmm_connect_succ ",dmm_connect_succ
		if dmm_connect_succ:

		    self.connect(self.timer, SIGNAL('timeout()'), self.on_timer)
		    self.timer.start(10)

		    self.status_text.setText('Monitor running')
		else:
			print "DMM NOT CONNECTED "
    
    def OnStop(self):
    	self.button_Connect.setEnabled(True)
        self.button_Disconnect.setEnabled(False)
        if not self.measure_voltage.isChecked():
        	self.measure_voltage.setEnabled(True)
    	if not self.measure_current.isChecked():
        	self.measure_current.setEnabled(True)
        if not self.measure_resistance.isChecked():
        	self.measure_resistance.setEnabled(True)
        if self.dmm_monitor is not None:
            self.dmm_monitor.join(1000)
            self.dmm_monitor = None
        self.monitor_active = False

        self.timer.stop()
        self.status_text.setText('Monitor idle')

    def on_timer(self):
        """ Executed periodically when the monitor update timer
            is fired.
        """
        print "temp samples   ",len(self.temperature_samples)
        print "data_q length    ",len(self.data_q)
        if len(self.data_q)!=0:
	        # print "data output  ",self.data_q 
	        # print "recent data  ",self.data_q[-1]
	        # tdata=[float(self.data_q[-1][1])]
	        # data_output=[float(self.data_q[-1][0].split(' ')[0])]
	        # print "tdata  ",tdata
	        # print "data_output  ",data_output
	        # self.x = arange(0.0, 100.1, 0.5)
	        # print "x value  ",self.x
	        # self.y = zeros(len(self.x), Float)
	        # print "y value  ",self.y
	        # self.y = concatenate((self.y[:1], self.y[:-1]), 1)
        	# self.y[0] = random.random()
	        # self.curve[0].setData(self.x,self.y)

            self.temperature_samples.append((float(self.data_q[-1][1]),float(self.data_q[-1][0].split(' ')[0])))
            xdata = [s[0] for s in self.temperature_samples]
            ydata = [s[1] for s in self.temperature_samples]
            self.plot.setAxisScale(Qwt.QwtPlot.xBottom,min(xdata[0],xdata[-1]+20),min(xdata[-1]+20))
            
            # self.plot.setAxisScale(Qwt.QwtPlot.xBottom, xdata[0], max(20, xdata[-1]))
            self.curve[0].setData(xdata, ydata)
            #self.plot.setAxisScale(Qwt.QwtPlot.xBottom, float(self.data_q[-1][1]), float(self.data_q[-1][0].split(' ')[0]) )        
            self.plot.replot()

	
def main():
    app = QApplication(sys.argv)
    form = PlottingDataMonitor()
    form.resize(800, 800)
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()