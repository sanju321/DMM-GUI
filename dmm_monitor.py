import Queue, threading, time, serial

class DmmMonitorThread(threading.Thread):
    """ A thread for monitoring a DMMUSB port. The DMMUSB port is 
        opened when the thread is started.
    
        data_q:
            list for received data. Items in the queue are
            received data from dmm respective of voltage,current
            ,resistance.
        
        error_q:
            list for error messages. In particular, if the 
            serial port fails to open for some reason, an error
            is placed into this queue.
        
        measure_input:
            voltage/current/resistance
    """
    
    def __init__(   self, data_q, error_q,measure_input):
        threading.Thread.__init__(self)
        
        self.serial_port = None
        
        self.data_q   = data_q
        self.error_q  = error_q
        
        self.measure_input=measure_input
        
        if self.measure_input=="voltage":
            self.measure_cmd="VDC\n"

        if self.measure_input=="current":
            self.measure_cmd="ADC\n"
        
        if self.measure_input=="resistance":
            self.measure_cmd="OHMS\n"
        

        self.alive    = threading.Event()
        self.alive.set()
    #------------------------------------------------------
    def DMM_capture_init(self):

        '''sets DMM for reading values. 
        global variables--DMM_serial_comm
        @return:True/False
        '''
        self.serial_port.write("\n")
        time.sleep(0.4)
        self.serial_port.flushInput()
        self.serial_port.write("RATE F\n")
        self.serial_port.flushInput()

        self.serial_port.write(self.measure_cmd)
        ip = self.serial_port.readline()
        
        if ip == '=>\r\n':
            print "GO"
            time.sleep(0.1)
            self.serial_port.flushInput()
            self.serial_port.write("LWLS\n")
            ip = self.serial_port.readline()
            if ip == '=>\r\n':
                return True
            else:
                return False
        else:
            return False

    def run(self):
        
        try:
            if self.serial_port: 
                self.serial_port.close()
            for i in range(0,50):
                print "value of i",i
                try:
                    self.serial_port = serial.Serial(port='/dev/ttyUSB'+str(i), baudrate=9600,timeout = 10)
                    print 80*'-',"DMM_serial_comm : ",'/dev/ttyUSB'+str(i),'\n',80*'-'
                    break
                except:
                    nothing = 1
        except Exception as e:
            self.error_q.append(e.message)
            return False
        print self.serial_port
        if self.serial_port!=None:
            if not self.DMM_capture_init():
                return False

            # Restart the clock
            startTime = time.time()
            
            while self.alive.isSet():
                
                print time.time()
                time.sleep(0.005)
                self.serial_port.flushInput()
                print "going to read value"
                self.serial_port.write("VAL1?\n")#for dc voltage meter measurement
                dmm_output = self.serial_port.readline()

                print "dmm_output  ",dmm_output
                timestamp = time.time() - startTime
                print "timestamp   ",timestamp
                #timestamp = time.clock()
                self.data_q.append((dmm_output,timestamp))
                self.serial_port.flushInput()
            # clean up
            if self.serial_port:
                self.serial_port.close()
        else:
            print "DMM serial Port Not connected "

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)

