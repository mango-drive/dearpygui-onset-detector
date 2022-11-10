import numpy as np
from pathlib import Path
import soundfile as sf
import time
import os


def calc_h(x, fS, fC, b):
    # https://fiiir.com/
    # https://tomroelandts.com/articles/how-to-create-a-simple-low-pass-filter
    b = b / fS
    N = int(np.ceil((4 / b)))
    if not N % 2:
        N += 1  # Make sure that N is odd.
    h = np.sinc(2 * fC / fS * (np.arange(N) - (N - 1) / 2))
    h *= np.hamming(N)
    h /= np.sum(h)
    return h, N


def fr(x, fS, fC, b):
    L = 1024
    h, N = calc_h(x, fS, fC, b)
    h_padded = np.zeros(L)
    h_padded[0:N] = h
    H = np.abs(np.fft.fft(h_padded)[0 : L // 2 + 1])
    return H


def lpf(x, sr, fc, b):
    h, N = calc_h(x, sr, fc, b)
    return np.convolve(x, h)


def hpf(x, sr, fc, b):
    h, N = calc_h(x, sr, fc, b)
    h = -h
    h[(N - 1) // 2] += 1
    return np.convolve(x, h)


def to_mono(f, of):
    print(f"Converting {f} to mono...")
    os.system(f"ffmpeg -nostats -loglevel 0 -y -i {f} -ac 1 {of}")
    return of


def envelope(x, decay_factor=0.9998):
    _x = np.abs(x)
    e = np.zeros_like(_x)
    e[0] = -1000
    for i, xi in enumerate(_x):
        if xi >= e[i - 1]:
            e[i] = xi
        else:
            e[i] = decay_factor * e[i - 1]
    return e


def derivative(x):
    return np.gradient(x)


def post_process(d):
    avg = np.average(d)
    _d = d - avg
    max = np.amax(d)
    _d = d / max
    return _d


def sliding_window(a, i, M, le):
    if i < M:
        l = 0
        r = 2 * M - 1
    elif i > le - 2 * M:
        l = le - 2 * M
        r = le - 1
    else:
        l = i - M
        r = i + M
    return a[l:r]


def sliding_mean(p, window_length):
    m = np.zeros_like(p)
    for i in range(len(p)):
        w = sliding_window(p, i, window_length, len(p))
        m[i] = np.mean(w)
    return m


def adaptive_threshold(p, t, l, window_length=4096):
    return t + l * sliding_mean(p, window_length)


def onsets(x, decay_factor, thresh):
    d = post_process(derivative(envelope(x, decay_factor)))
    idxs = np.where(d > thresh)[0]
    return (idxs, d[idxs])
    
def detect_onsets_in_post(post, thresh):
    idxs = np.where(post > thresh)
    return idxs[0].tolist()


def load_audio(fn):
    
    mono_file = Path(fn).stem + ".mono.wav"

    if not os.path.isfile(mono_file):
        to_mono(fn, mono_file)
    x, sr = sf.read(mono_file)
    return x, sr


def pick_events(fn, r):
    x, lf, hf, sr = load_audio(fn)
    s = 0.9999853
    t = 0.346
    ons = [onsets(_x, s, t) for _x in [lf, hf]]

    N = int((len(x) / sr) * r / 2)
    e = []
    for bons in ons:
        idxs, weights = bons
        weights = np.array(weights)
        weights = weights / np.sum(weights)
        c = np.random.choice(idxs, size=N, replace=False, p=weights)
        e.extend(c)
    return np.array(e) / sr


def detect_onsets(signal, decay_factor=0.99998, t=0.1, l=200, window_length=256, units='samples', sr=None):
    env = envelope(signal, decay_factor=decay_factor)
    deriv = derivative(env)
    post = post_process(deriv)
    thresh = adaptive_threshold(post, t, l, window_length)
    onset_idxs = detect_onsets_in_post(post, thresh)

    if units == 'time':
        assert sr is not None
        onset_idxs = [onset_idx / sr for onset_idx in onset_idxs]

    return env, deriv, post, thresh, onset_idxs






