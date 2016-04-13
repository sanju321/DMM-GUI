__author__ = 'azoi'
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from dmm_monitor import DmmMonitorThread
import pyqtgraph as pg
import sys,time
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
handler = logging.FileHandler('DMMLOG.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class Ui_Dialog(QDialog):
    def __init__(self):
        QDialog.__init__(self)
        self.setupUi()

    def setupUi(self):
        self.select_file_btn = QPushButton(self)
        self.select_file_btn.setText("Select File")
        self.select_file_btn.clicked.connect(self.showDialog)
        self.analyze_plot = pg.PlotWidget()
        self.pl = self.analyze_plot.plot()
        self.pl.setPen((200,200,100))
        self.layout = QGridLayout()
        self.layout.addWidget(self.select_file_btn,1,0)
        self.layout.addWidget(self.analyze_plot, 0, 0, 1, 0)
        self.setLayout(self.layout)

    def showDialog(self):
        fname = QFileDialog.getOpenFileName(self, 'Open file', '/home')

        logger.info("selected file name ",fname)
        try:
            f = open(fname, 'r')
            self.temperature_samples=[]
            data = f.readline().replace("\n", '')
            while f.readline():

                data1=f.readline().replace("\n",'').split(",")
                if len(data1)>1:

                    self.temperature_samples.append((float(data1[0]),float(data1[1])))
                    xdata = [s[0] for s in self.temperature_samples]
                    ydata = [s[1] for s in self.temperature_samples]

                    self.pl.setData(xdata, ydata)
        except Exception as e:
            logger.info("Error in selecting File ",e)


class PlottingDataMonitor(QMainWindow):
    def __init__(self, parent=None):
        super(PlottingDataMonitor, self).__init__(parent)

        self.monitor_active = False

        self.dmm_monitor=None
        self.temperature_samples = []
        self.timer = QTimer()
        self.create_main_frame()
        self.create_status_bar()
        # Activate start-stop button connections
        self.connect(self.Start_btn, SIGNAL("clicked()"),self.OnStart)
        self.connect(self.Stop_btn, SIGNAL("clicked()"),self.OnStop)
        self.connect(self.analyze_btn, SIGNAL("clicked()"),self.OnAnalyze)


    def create_main_frame(self):
        ## Create some widgets to be placed inside
        self.Start_btn = QPushButton('Start')
        self.Stop_btn=QPushButton('Stop')
        self.analyze_btn=QPushButton('Analyzes')

        self.Stop_btn.setEnabled(False)
        self.measure_voltage=QRadioButton('voltage')
        self.measure_current=QRadioButton('current')
        self.measure_resistance=QRadioButton('resistance')
        self.measure_voltage.setChecked(True)
        self.plot = pg.PlotWidget()
        self.pl = self.plot.plot()
        self.pl.setPen((200,200,100))

        ## Create a grid layout to manage the widgets size and position
        self.layout = QGridLayout()
        ## Define a top-level widget to hold everything
        self.w = QWidget()
        self.w.setLayout(self.layout)

        ## Add widgets to the layout in their proper positions
        self.layout.addWidget(self.Start_btn, 2, 0)   # start button
        self.layout.addWidget(self.Stop_btn, 3, 0)   # Stop button
        self.layout.addWidget(self.analyze_btn, 3, 1)   # analyze button

        self.layout.addWidget(self.measure_voltage, 2, 1)  # voltage
        self.layout.addWidget(self.measure_current, 2, 2)  # current
        self.layout.addWidget(self.measure_resistance, 2, 3)  # resistance
        self.layout.addWidget(self.plot, 0, 0, 2, 0)  # plot

        self.setCentralWidget(self.w)

    def OnAnalyze(self):

    	dialog_ui = Ui_Dialog()
        dialog_ui.exec_()

    def create_status_bar(self):
        self.status_text = QLabel('Monitor idle')
        self.statusBar().addWidget(self.status_text, 1)

    def OnStart(self):
        logger.info("Start CLicked ")
        self.Start_btn.setEnabled(False)
        self.Stop_btn.setEnabled(True)
        self.measure_input=''
        p1=self.plot.plotItem
        if not self.measure_voltage.isChecked():
            self.measure_voltage.setEnabled(False)
        else:
            self.measure_input='voltage'
            p1.setLabel('left',text='voltage',units='V')

        if not self.measure_current.isChecked():
            self.measure_current.setEnabled(False)
        else:
            self.measure_input='current'
            p1.setLabel('left',text='current',units='A')


        if not self.measure_resistance.isChecked():
            self.measure_resistance.setEnabled(False)
        else:
            self.measure_input='resistance'
            p1.setLabel('left',text='resistance',units='ohms')

        p1.setLabel('bottom',text='Time',units='sec')

        self.monitor_active = True
        self.temperature_samples=[]
        self.data_q      =  []
        self.error_q     =  []

        try:
            #starting Dmm Thread
            self.dmm_monitor =  DmmMonitorThread(self.data_q,self.error_q,self.measure_input)
            print self.dmm_monitor
            dmm_connect_succ=self.dmm_monitor.start()
            print "dmm_connect_succ ",dmm_connect_succ

            # if dmm_connect_succ:

            self.connect(self.timer, SIGNAL('timeout()'), self.on_timer)
            self.timer.start(50)#for plotting 20 samples per second every 50 ms we have to call ontimer()50 ms *20 samples=1000==1sec

            self.status_text.setText('Monitor running')
            # else:
            #     print "DMM NOT CONNECTED "
        except Exception as e:
            logger.info("Error in connecting with DMM or reading from DMM ",e)


    def OnStop(self):

        logger.info("Stop Clicked ")
        self.Start_btn.setEnabled(True)
        self.Stop_btn.setEnabled(False)
        if not self.measure_voltage.isChecked():
            self.measure_voltage.setEnabled(True)
        if not self.measure_current.isChecked():
            self.measure_current.setEnabled(True)
        if not self.measure_resistance.isChecked():
            self.measure_resistance.setEnabled(True)
        self.monitor_active = False
        self.status_text.setText('Monitor idle')

        if self.dmm_monitor is not None:
            self.dmm_monitor.join(1000)#join after 1 second
            self.dmm_monitor = None
        self.timer.stop()#stop timer

    def on_timer(self):
        """ Executed periodically when the monitor update timer
            is fired.
        """

        try:
            if len(self.data_q)!=0:
                self.temperature_samples.append((float(self.data_q[-1][1]),float(self.data_q[-1][0].split(' ')[0])))
                xdata = [s[0] for s in self.temperature_samples]
                ydata = [s[1] for s in self.temperature_samples]
                self.pl.setData(xdata,ydata)
        except Exception as e:
            logger.info("Error in plotting Data from Dmm Thread ",e)


def main():
    app = QApplication(sys.argv)
    form = PlottingDataMonitor()
    form.setWindowTitle("DMM Plotter")
    form.resize(800, 800)
    form.show()
    app.exec_()

if __name__ == "__main__":
    main()






