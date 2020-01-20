import scipy
import numpy as np
import matplotlib as mp
import matplotlib.pyplot as plt
from scipy import signal
from scipy import fft


raw_data = 'D:/Jason/Desktop/GRC Flows/rf socket_ch1 and ch3_17Jan2020.dat'
f = scipy.fromfile(open(raw_data), dtype = scipy.float32)
#trim the input for development
#f = f[19300000:20330000]
print('{} data points imported'.format(len(f)))
#looks like ~389 symbols per second (baud)
#"finite difference" or "discrete difference" is a rough estimate of derivative

fs = 2.4e6 #sample rate
f0 = 433e6 #carrier wave freq
fbaud = 6000 #symbols per second
lowcut = 100e6 #low cutoff freq (Hz)
highcut = 650e6 #high cutoff freq (Hz)

nsamples = len(f)
T = nsamples/fs
t = np.linspace(0, T, nsamples, endpoint=False)

#create an envelope detector and then low-pass filter, taken from https://www.allaboutcircuits.com/technical-articles/fsk-explained-with-python/
y_diff = np.diff(f[:nsamples]) #generate 1st derivative of the signal
f = None
print('Derivative of data calculated')

#downsample by a factor of 100 (tried 100  still has 20 points for the short pulse, but 200, 500, and 1000 didn't have enough points)
y_decimated = signal.decimate(signal.decimate(y_diff, 10), 10)
y_diff = None
print('Data downsampled to {} samples'.format(len(y_decimated)))

#adjust fs, nsamples, T, and t to account for decimation
dilution = int(nsamples / len(y_decimated))
fs_dec = fs / dilution
fbaud_dec = fbaud / dilution
nsamples_dec = len(y_decimated)
T_dec = nsamples_dec / fs
t_dec = np.linspace(0, T_dec, nsamples_dec, endpoint = False)

#separate full data file into list of pulses
messages = []
mean_sig = np.mean(np.abs(y_decimated))
breaks = {0}
crit_len = 4 #num samples of no pulse to split signal at
message_len = 0
silence_len = 0
for count in range(nsamples_dec):
    
    message_len = message_len + 1
    
    if abs(y_decimated[count]) < mean_sig:
        silence_len = silence_len + 1
    else:
        silence_len = 0
    
    if silence_len >= crit_len * fbaud_dec:
        message = y_decimated[max(0, count-message_len):count-silence_len]
        silence_len = 0
        if message.any():
            messages.append(message)
        message = None
        message_len = 0
        breaks.add(count-silence_len)
    
messages.append(y_decimated[max(breaks):]) #added at the end to save the end of the signal

y_decimated = None
envs = []

for message in messages:
    y_hilbert = signal.signaltools.hilbert(message)
    #hilberts.append(y_hilbert)
    print('Hilbert transform completed; analytic signal extracted')
    y_env = np.abs(y_hilbert)
    y_hilbert = None
    envs.append(y_env)
    y_env = None
    print('Baseband envelope calculated')

h = signal.firwin(numtaps = int(fbaud_dec), cutoff = fbaud_dec * 2, fs = fs_dec)  #using new decimation-corrected fbauds and fs's

messages = None
data = []

for env in envs:
    y_filtered = signal.lfilter(h, 1.0, env)
    print('FIR filter applied')
    y_filtered_dig = np.round(y_filtered / max(y_filtered))
    print('Samples digitized to 0s and 1s')
    y_filtered = None
    data.append(y_filtered_dig)
    y_filtered_dig = None

env = None
envs = None
answers = []
for message in data:
    sleep_flag = True
    pulse_len = 0
    short_len = 18
    decoded = 0b0
    for i in range(len(message)):
        last = message[max(0, i-1)]
        if message[i] <= last and sleep_flag:
            continue #sleep until either there's a rising edge or sleep_flag is false (i.e. we're decode)
        elif message[i] < last and not sleep_flag: #detect a falling edge while decoding
            sleep_flag = True
            decoded = decoded * 2 #left shift wasn't working reliably?
            if pulse_len > short_len * 2: #long pulse detected, decode as a 1
                decoded = decoded + 1
            else:
                decoded = decoded + 0
            pulse_len = 0
            continue
        sleep_flag = False
        pulse_len = pulse_len + 1
    if decoded > 0:
        #answers.append(decoded & 0b1111) #only keep the least significant 4 bits, everything else looks identical.
        answers.append(decoded)
print('Decoded pulses')
print([bin(x) for x in answers])
print([hex(x) for x in answers])
#0101 vs 1101 = same switch, different on/off
#1001 vs 0001 = same switch, different on/off
#looks like 4th bit (2^3) is on/off, lower 3 bits are switch ID

#show the pulses if there's a reasonable number of them...
if len(data) < 7:
    for x in range(len(data)):
        plt.subplot(len(data), 1, x+1)
        plt.plot(data[x])
        plt.title('Signal #' + str(x))
    #plt.plot(t_dec, y_filtered_dig)
    #plt.title('Filtered, Digitized')
    plt.tight_layout()
    plt.show()