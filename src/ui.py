

import os
from threading import Thread

import dearpygui.dearpygui as dpg
import soundfile as sf

from audio import *

def create_data(signal, decay_factor=0.99995):
    env = envelope(signal, decay_factor=decay_factor)
    deriv = derivative(env)
    post = post_process(deriv)
    thresh = adaptive_threshold(post, 0.1, 200)
    onset_idxs = detect_onsets_in_post(post, thresh)

    return env, deriv, post, thresh, onset_idxs


def clear_signals():
    dpg.set_value('sig', [[], []])
    dpg.set_value('env_sig', [[], []])
    dpg.set_value('post_sig', [[], []])
    dpg.set_value('thresh_sig', [[], []])
    dpg.set_value('onset_idxs', [[]])

def apply_filter(sender, *args):
    global current_signal
    value = dpg.get_value(sender)
    clear_signals()
    if value == 'hp_filter':
        current_signal = hpf(y, sr, 1000, 2)
    if value == 'lp_filter':
        current_signal = lpf(y, sr, 200, 2)
    if value == 'no_filter':
        current_signal = y
    dpg.set_value('sig', [x, current_signal])
    update_data()
    

def update_data(decay_factor=0.999):
    global x, current_signal
    global env, deriv, post, thresh, onset_idxs
    env, deriv, post, thresh, onset_idxs = create_data(current_signal, decay_factor=decay_factor)
    dpg.set_value("env_sig", [x, env])
    dpg.set_value("post_sig", [x, post])
    dpg.set_value("thresh_sig", [x, thresh])
    dpg.set_value("onset_idxs", [onset_idxs])


def decay_factor_changed(sender, app_data, user_data):
    update_data(dpg.get_value(sender) / 1000)

if __name__ == '__main__':
    # creating data
    audio_file = 'data/audio/hiphop.mono.wav'
    assert os.path.isfile(audio_file)
    y, sr = sf.read(audio_file)
    x = list(range(len(y)))
    current_signal = y
    
    env, deriv, post, thresh, onset_idxs = create_data(current_signal)

    dpg.create_context()
    WIDTH = 1000
    HEIGHT = 500

    with dpg.window(tag='main_window'):
        # create plot
        with dpg.subplots(3, 1, label='Onset Detector', width=WIDTH, height=HEIGHT, link_all_x=True, tag='plots') as subplot_id:
            # optionally create legend
            with dpg.plot(label='Envelope Follower'):
                dpg.add_plot_legend()
                dpg.add_plot_axis(dpg.mvXAxis, label='t', tag='sample_num_ax1')
                dpg.fit_axis_data(dpg.last_item())
                dpg.add_plot_axis(dpg.mvYAxis, label='x', tag='amplitude')
                dpg.set_axis_limits(dpg.last_item(), -1, 1)
                dpg.add_line_series(x, y, parent='amplitude', tag='sig')
                dpg.add_line_series(x, env, parent='amplitude', tag='env_sig')
            
            with dpg.plot(label='Threshold'):
                dpg.add_plot_axis(dpg.mvXAxis, label='t', tag='sample_num_ax2')
                dpg.add_plot_axis(dpg.mvYAxis, label='x', tag='thresh_amp')
                dpg.set_axis_limits(dpg.last_item(), 0, 1)
                dpg.add_line_series(x, post, parent='thresh_amp', tag='post_sig')
                dpg.add_line_series(x, thresh, parent='thresh_amp', tag='thresh_sig')

            with dpg.plot(label='Detected Onsets'):
                dpg.add_plot_axis(dpg.mvXAxis, label='t', tag='sample_num_ax3')
                dpg.add_plot_axis(dpg.mvYAxis, label='x', tag='onset_line')
                dpg.set_axis_limits(dpg.last_item(), 0, 1)
                dpg.add_vline_series(onset_idxs, tag='onset_idxs', parent='sample_num_ax3')

    with dpg.window(pos=(WIDTH+30,0)):
        dpg.add_radio_button(items=['no_filter', 'hp_filter', 'lp_filter'], tag='filter_radio', callback=apply_filter)
        dpg.add_slider_float(label="decay_factor", min_value=999, max_value=1000, callback=decay_factor_changed, tag='decay_slider')

    dpg.create_viewport(title='Onset Detector Demo')
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()
