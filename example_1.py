import sys, os, csv,random
import matplotlib
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar
from matplotlib.figure import Figure
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import PyQt4.Qwt5 as Qwt

class PlottingDataMonitor(QMainWindow):
    def __init__(self, parent=None):
        super(PlottingDataMonitor, self).__init__(parent)

        self.monitor_active = False 

        self.timer = QTimer()
        self.create_main_frame()
        self.create_status_bar()
        # Activate start-stop button connections
        self.connect(self.button_Connect, SIGNAL("clicked()"),
                    self.OnStart)
        self.connect(self.button_Disconnect, SIGNAL("clicked()"),
                    self.OnStop)

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
        plot.setCanvasBackground(Qt.black)
        plot.setAxisTitle(Qwt.QwtPlot.xBottom, 'Time')
        plot.setAxisScale(Qwt.QwtPlot.xBottom, 0, 10, 1)
        plot.setAxisTitle(Qwt.QwtPlot.yLeft, 'Voltage')
        plot.setAxisScale(Qwt.QwtPlot.yLeft, 0, 250, 40)
        plot.replot()
        return plot

    def create_status_bar(self):
        self.status_text = QLabel('Monitor idle')
        self.statusBar().addWidget(self.status_text, 1)

    def create_main_frame(self):

    	#start and stop reading button
    	portname_layout = self.create_com_box()
    	self.com_box.setLayout(portname_layout)
    	# Plot 
        self.plot = self.create_plot()
        plot_layout = QVBoxLayout()
        plot_layout.addWidget(self.plot)
        plot_groupbox = QGroupBox('Plot')
        plot_groupbox.setLayout(plot_layout)
        
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
        if not self.measure_voltage.isChecked():
        	self.measure_voltage.setEnabled(False)
    	if not self.measure_current.isChecked():
        	self.measure_current.setEnabled(False)
        if not self.measure_resistance.isChecked():
        	self.measure_resistance.setEnabled(False)

        self.monitor_active = True

        self.connect(self.timer, SIGNAL('timeout()'), self.on_timer)
            	
    
    def OnStop(self):
    	self.button_Connect.setEnabled(True)
        self.button_Disconnect.setEnabled(False)
        if not self.measure_voltage.isChecked():
        	self.measure_voltage.setEnabled(True)
    	if not self.measure_current.isChecked():
        	self.measure_current.setEnabled(True)
        if not self.measure_resistance.isChecked():
        	self.measure_resistance.setEnabled(True)

    def on_timer(self):
        """ Executed periodically when the monitor update timer
            is fired.
        """
        self.read_serial_data()
        self.update_monitor()

def main():
    app = QApplication(sys.argv)
    form = PlottingDataMonitor()
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()