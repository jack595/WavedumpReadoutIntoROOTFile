# -*- coding:utf-8 -*-
# @Time: 2023/12/13 10:44
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: WaveformRecTool.py
import matplotlib.pylab as plt
import numpy as np
import pandas as pd
import dask.dataframe as dd

plt.style.use("/afs/ihep.ac.cn/users/l/luoxj/Style/Paper.mplstyle")
import sys

sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/root_tool/python_script/")

def GetChannelList(item, return_number=True, prefix_channel="waveform_ch"):
    """

    :param item:
    :param return_number:
    :param input_Dataframe: True: we will get channel list from DataFrame.columns;False: item is dict, we will get list
    from item.keys()
    :return:
    """
    list_full = item.columns if isinstance(item, pd.DataFrame) or isinstance(item, dd.DataFrame)  else item.keys()
    waveform_columns = [col for col in list_full if col.startswith(prefix_channel)]

    # Extract the number after the string "waveform_ch" from each column name
    waveform_channel_numbers = [int(col.split(prefix_channel)[1]) for col in waveform_columns]
    if return_number:
        return waveform_channel_numbers
    else:
        return waveform_columns


def RecCharge(df:pd.DataFrame, integra_range:tuple):
    """

    :param df: the Dataframe converted from our DataReader which should contain "waveform_ch*" in columns
    :param integra_range:  range to get the charge
    :return:
    """
    v_channel_numbers = GetChannelList(df)
    for channel in v_channel_numbers:
        df[f"Q{channel}"] = df.apply(lambda row:
                                     np.sum(row[f"waveform_ch{channel}"][integra_range[0]:integra_range[1]]),
                                     axis=1)

def CreateButterFilter(cutoff_freq = 250e6, order = 4, fs = 1e9):
    """
    Create filter for function LowPassFilter()
    :param cutoff_freq:
    :param order:
    :param fs:
    :return:
    """
    from scipy import signal
    b, a = signal.butter(order, cutoff_freq, fs=fs, btype='low', analog=False)
    return (b, a)

def WaveformRec(data:dict,  filter_pars:list=None ):
    import pandas as pd
    from DataReader import SubtractBaseline,LowPassFilter, GetBaselineByMean

    # Turn Into Dataframe
    baseline_amp = 3
    n_baseline = 100
    df = pd.DataFrame.from_dict(data)
    df.reset_index(inplace=True)

    v_channel_numbers = GetChannelList(df)
    for channel in v_channel_numbers:
        SubtractBaseline(df, n_baseline=n_baseline, negative=True, TurnADC2mV=True,
                     Digitizer="751",  hist_find_baseline=True, baseline_amp=baseline_amp,
                        key_waveform=f"waveform_ch{channel}", key_waveform_output=f"waveform_sub_base_ch{channel}")
        df.drop(f"waveform_ch{channel}", inplace=True,axis=1)

    if not filter_pars is None:
        for channel in v_channel_numbers:
            LowPassFilter(df, filter_pars, n_baseline=n_baseline, baseline_amp=baseline_amp,
                          key_waveform=f"waveform_sub_base_ch{channel}",
                          key_waveform_output=f"waveform_sub_base_filter_ch{channel}")
            df.drop(f"waveform_sub_base_ch{channel}", inplace=True, axis=1)
            dict_rename_waveform = {f"waveform_sub_base_filter_ch{channel}":f"waveform_sub_base_ch{channel}"}
            df.rename(columns=dict_rename_waveform, inplace=True)
    return df

############################################################################################
################################# Events Cut ###############################################
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~  Get Basic Property ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def GetBasicProperty(df_concat:pd.DataFrame, dict_SPE, Q_range = (400, 600), max_range = (300, 600)):
    v_channels = GetChannelList(df_concat)
    for name_channel in v_channels:
        df_concat[f"Q_win_ch{name_channel}"] = df_concat.apply(lambda row: np.sum(row[f"waveform_sub_base_ch{name_channel}"][Q_range[0]:Q_range[1]]),
                                                             axis=1)
        df_concat[f"Q_total_ch{name_channel}"] = df_concat.apply(lambda row: np.sum(row[f"waveform_sub_base_ch{name_channel}"]),
                                                            axis=1)
    for name_channel in v_channels:
        df_concat[f"NPE_win_ch{name_channel}"] = df_concat.apply(lambda row: row[f"Q_win_ch{name_channel}"]/dict_SPE[name_channel],
                                                             axis=1)
    for name_channel in v_channels:
        df_concat[f"std_total_ch{name_channel}"] = df_concat[f"waveform_sub_base_ch{name_channel}"].apply(lambda wave:np.std(wave))
        df_concat[f"max_total_ch{name_channel}"] = df_concat[f"waveform_sub_base_ch{name_channel}"].apply(lambda wave:np.max(np.abs(wave)))
        df_concat[f"min_total_ch{name_channel}"] = df_concat[f"waveform_sub_base_ch{name_channel}"].apply(lambda wave:np.min(wave))
        df_concat[f"std_ch{name_channel}"] = df_concat[f"waveform_sub_base_ch{name_channel}"].apply(lambda wave:np.std(wave[Q_range[0]:Q_range[1]]))
        df_concat[f"max_ch{name_channel}"] = df_concat[f"waveform_sub_base_ch{name_channel}"].apply(lambda wave:np.max(wave[max_range[0]:max_range[1]]))

    v_dt = np.diff(df_concat["TriggerTime"])
    v_dt = np.concatenate(([-1], v_dt))
    df_concat["dt"] = v_dt
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



