# requires rtl-sdr dlls in the same folder as script...
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy import stats

live_signal = False
fs = 2.4e6  # sample rate
f0 = 433e6  # carrier wave freq
fbaud = 6000  # symbols per second

if live_signal:
    from rtlsdr import RtlSdr
    sdr = RtlSdr()
    sdr.sample_rate = fs
    sdr.center_freq = f0
    sdr.freq_correction = 60
    sdr.gain = 'auto'
    f = sdr.read_samples(num_samples=fs * 5)
else:
    f = open('D:/Jason/Desktop/GRC Flows/rf socket_ch1 and ch3_17Jan2020.dat', 'rb').read()

g = np.abs(f)
print('{} data points imported'.format(len(g)))
nsamples = len(g)
y_decimated = signal.decimate(signal.decimate(g, 10), 10)
T = nsamples/fs
t = np.linspace(0, T, nsamples, endpoint=False)
print('Data downsampled to {} samples'.format(len(y_decimated)))

# adjust fs, nsamples, T, and t to account for decimation
# need a clever way of calculating dilution on the fly
dilution = 100
fs_dec = fs / dilution
fbaud_dec = fbaud / dilution
nsamples_dec = len(y_decimated)
T_dec = nsamples_dec / fs
t_dec = np.linspace(0, T_dec, nsamples_dec, endpoint=False)

# separate full data file into list of pulses
messages = []
mid_sig = np.max(np.abs(y_decimated)) / 3
breaks = {0}
crit_len = 5  # num samples of no-pulse to split signal at
message_len = 0
silence_len = 0
for count in range(nsamples_dec):

    message_len = message_len + 1

    if abs(y_decimated[count]) < mid_sig:
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
# added at the end to save the end of the signal
messages.append(y_decimated[max(breaks):])

mid_mean_sig = np.median([np.mean(x) for x in messages])

envs = []

for message in messages:
    if stats.skew(message) > 0.5 or stats.skew(message) < 0:
        messages.remove(message)
        continue
    y_hilbert = signal.signaltools.hilbert(np.real(message))
    y_env = np.abs(y_hilbert)
    y_hilbert = None
    envs.append(y_env)
    y_env = None

h = signal.firwin(numtaps=int(fbaud_dec),
                  cutoff=fbaud_dec*2,
                  fs=fs_dec)

data = []

for env in envs:
    y_filtered = signal.lfilter(h, 1.0, env)
    y_filtered_dig = np.round(y_filtered / max(y_filtered))
    y_filtered = None
    data.append(y_filtered_dig)
    y_filtered_dig = None

answers = []
for message in data:
    sleep_flag = True
    pulse_len = 0
    short_len = 18
    decoded = 0b0
    for i in range(len(message)):
        last = message[max(0, i-1)]
        # sleep until either there's a rising edge or
        # sleep_flag is false (i.e. we're decoding)
        if message[i] <= last and sleep_flag:
            continue
        # detect a falling edge while decoding
        elif message[i] < last and not sleep_flag:
            sleep_flag = True
            # tried bitwise leftshift, but it wasn't working reliably?
            decoded = decoded * 2
            # long pulse detected, decode as a 1
            if pulse_len > short_len * 2:
                decoded = decoded + 1
            # short pulse detected, decode as a 0
            else:
                decoded = decoded + 0
            pulse_len = 0
            continue
        sleep_flag = False
        pulse_len = pulse_len + 1
    if decoded > 0:
        answers.append(decoded)
print('Decoded pulses')
print([bin(x) for x in answers])
print([hex(x) for x in answers])

# show the pulses if there's a reasonable number of them...
if len(data) < 7:
    for x in range(len(data)):
        plt.subplot(len(data), 1, x+1)
        plt.plot(data[x])
        plt.title('Signal #' + str(x))
    plt.tight_layout()
    plt.show()
