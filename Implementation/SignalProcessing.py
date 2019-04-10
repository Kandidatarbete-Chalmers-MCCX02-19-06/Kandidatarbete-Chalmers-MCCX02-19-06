import numpy as np
from scipy import signal #Det här kanske behöver importeras på något annat sätt.
import matplotlib.pyplot as plt #TODO: ta bort sen
import time #TODO: Ta bort sen
from scipy.fftpack import fft
import threading
import queue

class SignalProcessing:

    def __init__(self,go, HR_filtered_queue, HR_final_queue, RR_filtered_queue, RR_final_queue): #TODO: Lägg till RR_filtered_queue och RR_final_queue
        self.go = go
        self.HR_filtered_queue = HR_filtered_queue
        self.HR_final_queue = HR_final_queue
        self.counter_fft = 0
        self.index_fft = 0
        self.sample_freq = 20 #TODO:Temporary

        # Variabler för Schmitt Trigger
        self.RR_filtered_queue = RR_filtered_queue
        self.RR_final_queue = RR_final_queue

        #Starta heart_rate
        self.heart_rate_thread = threading.Thread(target = self.heart_rate)
        self.heart_rate_thread.start()
        #Starta schmitt
        self.schmittTrigger = threading.Thread(target = self.schmittTrigger)
        self.schmittTrigger.start()
        

    def thread_start(self):         # used in Main to start and join the signal processing threads
        pass


    def heart_rate(self):
        T_resolution = 30
        overlap = 90
        beta = 1
        fft_window = np.zeros(T_resolution*self.sample_freq) # Data in vector with length of window
        i=0
        while self.go:
        #for i in range(3):
            [freq,fft_signal_out] = self.windowedFFT(fft_window, overlap, beta)
            print(i)
            i += 1


        plt.plot(freq,fft_signal_out)
        plt.grid()
        plt.show()
     

    ### windowedFFT ###
    ### input:
    # fft_window: array to be filled with filtered data. And then to be fft:d
    # overlap: how many overlapping values between two consecutive fft windows. [in percentage] 
    # beta: shape factor for kaiser window. 
    ### returns:
    # freq: corresponding frequency array
    # fft_signal_out: fft:d array
    def windowedFFT(self,fft_window, overlap, beta): 
        window_width = len(fft_window) #size of each window
        window_slide = int(np.round(window_width*(1-overlap/100))) #number of overlapping points


        for i in range(window_slide): # fills the fft_window array with window_slide values from filtered queue
            fft_window[self.index_fft] = HR_filtered_queue.get()
            self.index_fft += 1
            if self.index_fft == window_width-1:
                self.index_fft = 0
        
        fft_window = np.roll(fft_window, -(self.index_fft+1)) #TODO: Check if necessary
        [freq, fft_signal_out] = self.smartFFT(fft_window,beta) #do fft
        fft_window = np.roll(fft_window, (self.index_fft+1))
        return freq, fft_signal_out

        
    ### smartFFT ###
    ### input:
    # signal_in: in signal as an array
    # sample_freq: sample frequency
    # beta: shape factor for the window
    ### returns:
    # freq: frequency array [Hz] 
    # signal_out: fft of the in signal as an array 
    def smartFFT(self, signal_in, beta):
        length_seq = len(signal_in) #number of sequences
        window = np.kaiser(length_seq,beta) #beta: shape factor
        signal_in = np.multiply(signal_in,window) 

        signal_in_fft = fft(signal_in) #two-sided fft of input signal

        signal_fft_abs = abs(signal_in_fft/length_seq)
        signal_out = 2*signal_fft_abs[0:length_seq//2] # one-sided fft 

        freq = self.sample_freq*np.arange(length_seq/2)/length_seq # frequency array corresponding to frequencies in the fft

        return freq,signal_out

    def schmittTrigger(self):
        # variable declaration
        Tc = 5  # medelvärdesbildning över antal [s]
        schNy = 0  # Schmitt ny
        schGa = 0  # Schmitt gammal
        Hcut = 0.001  # Higher hysteres cut. Change this according to filter. To manage startup of filter
        Lcut = -Hcut  # Lower hysteres cut
        avOver = 30  # average over old values. TODO ev. ingen medelvärdesbildning. För att förhindra att andningen går mot ett fast värde. Vi vill se mer i realtid.
        freqArray = np.zeros(avOver)  # for averaging over old values
        count = 1  # for counting number of samples passed since last negative flank
        countHys = 1  # for counting if hysteresis should be updated
        FHighBR = 0.7  # To remove outliers in mean value
        FLowBR = 0.2  # To remove outliers in mean value
        # for saving respiratory_queue_BR old values for hysteresis
        trackedBRvector = np.zeros(self.sample_freq * Tc)  # to save old values

        while self.go:
            # to be able to use the same value in the whole loop
            trackedBRvector[countHys - 1] = self.RR_filtered_queue.get()

            if countHys == self.sample_freq * Tc:
                Hcut = np.sqrt(np.mean(np.square(trackedBRvector)))  # rms of trackedBRvector
                Lcut = -Hcut
                # TODO Hinder så att insvängningstiden för filtret hanteras
                countHys = 0

            schNy = schGa

            if trackedBRvector[countHys - 1] <= Lcut:  # trackedBRvector[countHys-1] is the current data from filter
                schNy = 0
                if schGa == 1:
                    np.roll(freqArray, 1)
                    freqArray[0] = self.sample_freq / count  # save the new frequency between two negative flanks
                    # Take the mean value
                    # RR_final_queue is supposed to be the breathing rate queue that is sent to app
                    self.RR_final_queue = self.getMeanOfFreqArray(freqArray, FHighBR, FLowBR)
                    # TODO put getMeanOfFreqArray() into queue that connects to send bluetooth values instead
                    count = 0
            # trackedBRvector[countHys-1] is the current data from filter
            elif trackedBRvector[countHys - 1] >= Hcut:
                schNy = 1
                # TODO skicka data till app för realTime breathing

            schGa = schNy
            count += 1
            countHys += 1

    # Used in schmittTrigger. Removes outliers and return mean value over last avOver values.
    def getMeanOfFreqArray(freqArray, FHighBR, FLowBR):  # remove all values > FHighBR and < FLowBR
        freqArrayTemp = [x for x in freqArray if (x < FHighBR and x > FLowBR)]
        # print(freqArrayTemp)
        freqArrayTemp = freqArrayTemp[np.nonzero(freqArrayTemp)]
        # print(freqArrayTemp)

        median = np.median(freqArrayTemp)  # median value
        stanDev = np.std(freqArrayTemp)  # standard deviation

        freqArrayTemp = [x for x in freqArrayTemp if (x > median - 3 * stanDev and x < median + 3 * stanDev)]
        # print(freqArrayTemp)
        mean = np.mean(freqArrayTemp)  # mean value of last avOver values excluding outliers
        return mean


## MAIN ##  TODO: Ta bort MAIN sen


#windowedFFT(data_in, sample_freq, T_resolution, overlap, beta)
HR_filtered_queue = queue.Queue()
HR_final_queue = queue.Queue()

sample_freq = 20
length_seq = 100000
sample_spacing = 1/sample_freq

t = np.arange(length_seq)*sample_spacing
signal_in = 4*np.sin(1 * 2.0*np.pi*t) + 0*np.sin(2 * 2.0*np.pi*t)
#print(signal_in)

for i in range(len(signal_in)):
    HR_filtered_queue.put(signal_in[i])

go =["True"]

signal_processing = SignalProcessing(HR_filtered_queue, HR_final_queue,go)

time.sleep(0.5)
go.pop(0)


#### Test av smartFFT ####
# sample_freq = 20
# length_seq = 600
# sample_spacing = 1/sample_freq

# t = np.arange(length_seq)*sample_spacing
# signal_in = 4*np.sin(1 * 2.0*np.pi*t) + 0.5*np.sin(4 * 2.0*np.pi*t)
# #signal_in = np.roll(signal_in, 5)
# beta = 1

# [freq,signal_out] = smartFFT(signal_in,sample_freq,beta)

# plt.plot(freq, signal_out)
# plt.grid()
# plt.show()