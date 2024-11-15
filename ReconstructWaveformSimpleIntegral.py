# -*- coding:utf-8 -*-
# @Time: 6/3/2024 4:27 PM
# @Author: Luo Xiaojie
# @Email: luoxj@ihep.ac.cn
# @File: ReconstructWaveformSimpleIntegral.py
import numpy as np
import sys

import pandas as pd
sys.path.append("/afs/ihep.ac.cn/users/l/luoxj/root_tool/python_script/")

from DataReader import CreateButterFilter
from DataReader import WaveDumpReader, SubtractBaseline, LowPassFilterForWave
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser("Reconstruct T/Q pairs from WaveDump ROOT file")
    parser.add_argument("--input",type=str, help="path of intput ROOT file(The ROOT file output from TurnWaveDumpDataIntoROOT.root)")
    parser.add_argument("--output",type=str, default="./test.root", help="path of output file(*.root)")
    parser.add_argument("--Digitizer",type=str, default="751", help="Specify Digitizer Type")
    parser.add_argument("--nEvts",type=int, default=-1, help="How many events to process in each file")
    parser.add_argument("--isNegative",type=int, default=1, help="Polarity of Signal")
    parser.add_argument("--Q-start", type=int, default=0, help="Start of Integration")
    parser.add_argument("--Q-end", type=int, default=-1, help="End of Integration")
    parser.add_argument("--n-baseline", type=int, default=100, help="Number of beginning waveform to get baseline")
    parser.add_argument("--baseline-amp", type=int, default=20, help="amplitude cut for finding baseline")
    parser.add_argument("--baseline-start", type=int, default=0, help="Beginning of Baseline")

    # For Low Pass Filter
    parser.add_argument("--SamplingRate", type=int, default=1000, help="Sampling Rate (Unit:MHz)")
    parser.add_argument("--CutOffFreq", type=int, default=100, help="CutOff Frequency (Unit:MHz)")

    parser.add_argument("--SplitSaving", "-s", default=True,  action="store_true",
                        help="Splitting Dataframe into several segment for memory optimization")
    parser.add_argument("--HistFindBaseline",  default=False,  action="store_true",
                        help="Fill Waveform into histogram to find baseline")

    args = parser.parse_args()
    Q_start = args.Q_start
    Q_end = None if args.Q_end==-1 else args.Q_end
    n_baseline = args.n_baseline
    baseline_start = args.baseline_start
    baseline_amp = args.baseline_amp
    hist_find_baseline = args.HistFindBaseline

    fs = args.SamplingRate*1e6
    cutoff_freq = args.CutOffFreq*1e6
    filter_pars = CreateButterFilter(fs=fs, cutoff_freq=cutoff_freq)

    from DataReader import SubtractBaselineForOneWaveform
    from StringTools import MatchWithTemplate
    from ROOT import TChain, gROOT, TTree, TFile
    from tqdm import trange
    from array import array
    gROOT.SetBatch(True)

    # Set Loading Chain
    chain = TChain("WaveDump")
    chain.Add(args.input)

    # Set TFile for Saving
    file = TFile.Open(args.output, "recreate")
    tree = TTree("WaveDump", "WaveDump")




    # Get List of Channels of Waveform
    template_waveform = "waveform_ch*"
    list_chain = chain.GetListOfBranches()
    v_name_channels = []
    for i in range(list_chain.GetEntries()):
        name_branch = list_chain.At(i).GetName()
        if "waveform_ch" in name_branch:
            channel = MatchWithTemplate(name_branch, template_waveform)[0]
            v_name_channels.append(channel)

    print("Available Channels:\t", v_name_channels)
    # dict_save_data = {"triggerTime":[]}
    # for channel in v_name_channels:
    #     dict_save_data["Q_"+str(channel)] = []
    #     dict_save_data["waveform_sub_base_"+str(channel)] = []
    #     dict_save_data["waveform_sub_base_filter_"+str(channel)] = []

    if args.nEvts == -1:
        nEvts = chain.GetEntries()
    else:
        nEvts = args.nEvts


    triggerTime_save = np.empty(1, "float64")
    for i_entry in trange(nEvts):
    # for i_entry in trange(chain.GetEntries()):
        chain.GetEntry(i_entry)

        if i_entry==0:
            length_wave = chain.length_waveform
            tree.Branch("triggerTime", triggerTime_save, "triggerTime/D")
            for channel in v_name_channels:
                name_branch = f"waveform_sub_base_filter_ch{channel}"
                locals()[name_branch] = array("f",  length_wave * [0.])
                tree.Branch(name_branch, locals()[name_branch], f"{name_branch}[{length_wave}]/F")


                for name_branch in [f"Q_ch{channel}", f"Amp_ch{channel}", f"Valley_ch{channel}"]:
                    locals()[name_branch] = np.empty(1, "float64")
                    tree.Branch(name_branch, locals()[name_branch], f"{name_branch}/D")




        # dict_save_data["triggerTime"].append(chain.triggerTime)
        triggerTime_save[0] = chain.triggerTime
        for channel in v_name_channels:
            wave_sub_baseline = SubtractBaselineForOneWaveform(np.array(getattr(chain, f"waveform_ch{channel}")),
                                                               negative=args.isNegative, TurnADC2mV=True,
                                                               hist_find_baseline=False, Digitizer=args.Digitizer,
                                                               baseline_start=baseline_start, n_baseline=n_baseline)
            wave_sub_baseline_filter = LowPassFilterForWave( wave_sub_baseline, filter_pars, n_baseline=n_baseline,
                                                             baseline_amp=baseline_amp, baseline_start=baseline_start)

            name_branch = f"waveform_sub_base_filter_ch{channel}"
            for k in range(len(wave_sub_baseline_filter)):
                locals()[name_branch][k] = float(wave_sub_baseline_filter[k])

            # dict_save_data["waveform_sub_base_"+str(channel)].append(wave_sub_baseline)
            # dict_save_data["waveform_sub_base_filter_"+str(channel)].append(wave_sub_baseline_filter)
            locals()[f"Q_ch{channel}"][0] = np.sum(wave_sub_baseline_filter[args.Q_start:args.Q_end])
            locals()[f"Amp_ch{channel}"][0] = np.max(wave_sub_baseline_filter[args.Q_start:args.Q_end])
            locals()[f"Valley_ch{channel}"][0] = np.min(wave_sub_baseline_filter[args.Q_start:args.Q_end])
        tree.Fill()
    tree.Write()
    file.Close()
    # df_save = pd.DataFrame.from_dict(dict_save_data)
    # df_save.to_hdf(args.output, key="df", mode="w")





