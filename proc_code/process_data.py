from __future__ import annotations

import datetime
import os
import json

import csv
from typing import List

from . import metadata
from . import path_tools
from . import load_data, types
from .nid import to_nid

from .utils import parse_float, parse_int, count_elements, verdict_bool, verdict_int, vertict_val


def process_supported(exp: types.Experiment, supported_trace: load_data.TraceEntry):
    parts = supported_trace.name.split("_")

    conn_type = "_".join(parts[1:-1])
    supp_type = parts[-1]

    def set_result(supp_type, selected):
        if supp_type == "ALL":
            if selected is not None:
                exp.results.support_results.preferred.append(selected)
                supp_type = selected

        if supp_type == "DIN":
            exp.results.support_results.din.append(selected)
        elif supp_type == "V2V10":
            exp.results.support_results.v2v10.append(selected)
        elif supp_type == "V2V13":
            exp.results.support_results.v2v13.append(selected)
        elif supp_type == "V20DC":
            exp.results.support_results.v20dc.append(selected)

        else:
            print(f"Unknown type {supp_type} in {exp.path}")

    for _, entry in supported_trace.traces():
        if entry.name == "supportedAppProtocolRes":
            for _, entry2 in entry.entries():
                if entry2.name == "DECODED":
                    if "<ResponseCode>Failed_NoNegotiation</ResponseCode>" in entry2.data:
                        set_result(supp_type, None)
                if entry2.name == "CHOSEN":
                    set_result(supp_type, entry2.data["name"])           

def process_conn_inner(exp: types.Experiment, conn_trace: load_data.TraceEntry):
    good = True
    for _, entry in conn_trace.entries():
        if entry.name == "EXCEPTION":
            good = False

    if exp.version is None:
        raise ValueError("Version not set")

    conn_type = conn_trace.trace[-2]
    if conn_type == "CONN_MTLS_V20":
        exp.results.tls_results.v13.append(good)
    elif conn_type == "CONN_UTLS_V2":
        exp.results.tls_results.v12.append(good)
    # Some software versions detected TLS 1.3 as weak and strong. Count here as unsure observation, delete later if TLS 1.3 is used.
    elif conn_type == "CONN_TLS12_STRONG":
        exp.results.tls_results.strong.append((2 if exp.version > 6 else 1) if good else 0)
    elif conn_type == "CONN_TLS12_WEAK":
        exp.results.tls_results.weak.append((2 if exp.version > 6 else 1) if good else 0)
    elif conn_type == "CONN_OLD_TLS":
        exp.results.tls_results.old.append(good)
    elif conn_type == "CONN_BAD_TRUSTED":
        pass
    else:
        print(f"Unknown connection type {conn_type}")

def process_conn(exp: types.Experiment, conn_trace: load_data.TraceEntry):
    for _, entry in conn_trace.traces():
        if entry.name == "NTLS":
            process_conn_inner(exp, entry)
        if entry.name == "UTLS":
            process_conn_inner(exp, entry)
        if entry.name == "MTLS":
            process_conn_inner(exp, entry)

def process_sdp_inner(exp: types.Experiment, sdp_trace: load_data.TraceEntry, tls: bool):
    for _, entry in sdp_trace.entries():
        if entry.name == "RES":
            exp.results.sdp_results.append(types.SDPResult(
                req_tls = tls,
                res_tls = entry.data["res"]["tls"],
                port = entry.data["res"]["port"],
            ))

def process_sdp(exp: types.Experiment, sdp_trace: load_data.TraceEntry):
    for _, entry in sdp_trace.traces():
        if entry.name == "SDP":
            process_sdp_inner(exp, entry, sdp_trace.name.endswith("YTLS"))

def process_slac(exp: types.Experiment, slac_trace: load_data.TraceEntry):
    for _, entry in slac_trace.entries():
        if entry.name == "SLAC":
            #Fix bugs in early data collectors
            if entry.data["EVSE_ID"] == entry.data["EVSE_MAC"]:
                entry.data["EVSE_ID"] = ""
            if entry.data["EVSE_MAC"] == entry.data["PEV_MAC"]:
                entry.data["EVSE_MAC"] = ""

            if entry.data["NMK"] is not None:
                exp.results.slac_nmk.append(
                    types.SlacNMKResult(
                        nmk = entry.data["NMK"],
                        nid = entry.data["NID"],
                        nid_match= (bytes.fromhex(entry.data["NID"]) == to_nid(bytes.fromhex(entry.data["NMK"]))),
                        random = None
                    )
                )
            if entry.data["AAG"] is not None:
                exp.results.slac_ids.append(
                    types.SlacSoundingResult(
                        evse_id= entry.data["EVSE_ID"],
                        evse_mac= entry.data["EVSE_MAC"],
                        aag= entry.data["AAG"]
                    )
                )
            

        if entry.name == "NETWORK":
            if entry.data is not None:
                for sta in entry.data["STATIONS"]:
                    if sta["MAC"] == entry.data["CCO_DA"]:
                        exp.results.hpgp.append(
                            types.HPGPCCoResult(
                                mac = sta["MAC"],
                                ident = sta["VERSION"]["IDENT"] if sta["VERSION"] is not None else "",
                                version = sta["VERSION"]["VERSION"] if sta["VERSION"] is not None else "",
                                mfg = sta["IDENTITY"]["MFG"] if sta["IDENTITY"] is not None else "",
                                usr = sta["IDENTITY"]["USR"] if sta["IDENTITY"] is not None else "",
                            )
                        )

# Experiment

def load_experiment(exp: types.Experiment) -> bool:
    processed_file_path = os.path.join(exp.path, "processed.json")
    if os.path.isfile(processed_file_path):
        with open(processed_file_path, "r") as f:
            j = json.load(f)
            exp.results.set_from_json(j)
            exp.time = j["time"]
        return True
    return False

def process_experiment(plug: types.Plug, exp: types.Experiment) -> bool:
    root_trace = load_data.read_result(exp.path)
    if root_trace is None:
        return False
    
    exp.version = root_trace.find_data("INFO")[0][1].data["v"]
    exp.time = root_trace.find_data("INFO")[0][1].time

    for _, entry in root_trace.traces():
        if entry.name == "SLAC":
            process_slac(exp, entry)
        if entry.name.startswith("SDP_"):
            process_sdp(exp, entry)
        if entry.name.startswith("CONN_"):
            process_conn(exp, entry)
        if entry.name.startswith("SUPPORTED_"):
            process_supported(exp, entry)

    review_path = os.path.join(plug.get_path(), "nmk_review.json")
    if os.path.isfile(review_path):
        with open(review_path) as f:
            val = json.load(f)
            for nmk in exp.results.slac_nmk:
                if nmk.nmk in val:
                    nmk.random = val[nmk.nmk]
    
    return True

def load_or_process_experiment(plug: types.Plug, exp: types.Experiment, run_policy: int) -> bool:
    #Must run fresh
    if run_policy >= 3:
        if process_experiment(plug, exp):
            return True
    #Try load
    if load_experiment(exp):
        return True
    #Allowed to run
    if run_policy == 1:
        return process_experiment(plug, exp)
    return False

def save_experiment(exp: types.Experiment):
    processed_file_path = os.path.join(exp.path, "processed.json")
    with open(processed_file_path, "w") as f:
        json.dump({"time": exp.time} | exp.results.to_json(), f)
        exp.results.disk_synced = True

def review_plug_nmk(plug: types.Plug):
    if plug.experiments is None:
        raise ValueError("No experiments to process")

    nmks = [nmk for exp in plug.experiments for nmk in exp.results.slac_nmk]

    need_review = False
    for nmk in nmks:
        if nmk.random is None:
            need_review = True
    if not need_review:
        return
    
    print("\n".join([data.nmk for data in nmks]))
    val = int(input("0: Pattern, 1: Partial, 2: Random? "))

    nmk_dict = {
        nmk.nmk: val for exp in plug.experiments for nmk in exp.results.slac_nmk
    }

    with open(os.path.join(plug.get_path(), "nmk_review.json"), "w") as f:
        json.dump(nmk_dict, f, indent=2)

    for exp in plug.experiments:
        for nmk in exp.results.slac_nmk:
            nmk.random = val
            exp.results.disk_synced = False

# Plug

def compact_results(self: types.Plug):
    if self.experiments is None:
        raise ValueError("Load experiments before compatcting")

    self.compacted = types.ExperimentResult()

    self.compacted.hpgp = [x for exp in self.experiments for x in exp.results.hpgp]
    self.compacted.slac_nmk = [x for exp in self.experiments for x in exp.results.slac_nmk]
    self.compacted.slac_ids = [x for exp in self.experiments for x in exp.results.slac_ids]
    self.compacted.sdp_results = [x for exp in self.experiments for x in exp.results.sdp_results]

    self.compacted.support_results.preferred = [x for exp in self.experiments for x in exp.results.support_results.preferred]
    self.compacted.support_results.din = [x for exp in self.experiments for x in exp.results.support_results.din]
    self.compacted.support_results.v2v10 = [x for exp in self.experiments for x in exp.results.support_results.v2v10]
    self.compacted.support_results.v2v13 = [x for exp in self.experiments for x in exp.results.support_results.v2v13]
    self.compacted.support_results.v20dc = [x for exp in self.experiments for x in exp.results.support_results.v20dc]

    self.compacted.tls_results.v13 = [x for exp in self.experiments for x in exp.results.tls_results.v13]
    self.compacted.tls_results.v12 = [x for exp in self.experiments for x in exp.results.tls_results.v12]
    self.compacted.tls_results.strong = [x for exp in self.experiments for x in exp.results.tls_results.strong]
    self.compacted.tls_results.weak = [x for exp in self.experiments for x in exp.results.tls_results.weak]
    self.compacted.tls_results.old = [x for exp in self.experiments for x in exp.results.tls_results.old]

def calculate_stats(self: types.Plug, experiment_times: List[str]):
    if self.compacted is None:
        compact_results(self)
    #Just to make type checker happy
    if self.compacted is None:
        raise ValueError("No data for statistics")

    self.reduced = types.ReducedResult()

    self.reduced.experiments = experiment_times

    self.reduced.nmk_random |= count_elements([x.random for x in self.compacted.slac_nmk if x.random is not None])
    self.reduced.nid_match |= count_elements([x.nid_match for x in self.compacted.slac_nmk])

    self.reduced.tls_support |= count_elements([x.res_tls for x in self.compacted.sdp_results if x.req_tls])
    self.reduced.tls_support_v13 |= count_elements([x for x in self.compacted.tls_results.v13])
    self.reduced.tls_support_v12 |= count_elements([x for x in self.compacted.tls_results.v12])
    strong_tmp = {0:0, 1:0, 2:0} | count_elements([x for x in self.compacted.tls_results.strong])
    weak_tmp = {0:0, 1:0, 2:0} | count_elements([x for x in self.compacted.tls_results.strong])
    if self.reduced.tls_support_v13[True] > 0:
        #Unsure observations from early software version that detecte TLS 1.3 as weak/strong ciphers
        strong_tmp[1] = 0
        weak_tmp[1] = 0
        print("Cleared")
    self.reduced.tls_support_strong |= {False: strong_tmp[0], True: strong_tmp[1] + strong_tmp[2]}
    self.reduced.tls_support_weak |= {False: strong_tmp[0], True: strong_tmp[1] + strong_tmp[2]}
    self.reduced.tls_support_old |= count_elements([x for x in self.compacted.tls_results.old])

    self.reduced.preferred |= count_elements([x for x in self.compacted.support_results.preferred])
    self.reduced.din_support |= count_elements([x == "DIN" for x in self.compacted.support_results.din])
    self.reduced.v2v10_support |= count_elements([x == "V2V10" for x in self.compacted.support_results.v2v10])
    self.reduced.v2v13_support |= count_elements([x == "V2V13" for x in self.compacted.support_results.v2v13])
    self.reduced.v20dc_support |= count_elements([x == "V20DC" for x in self.compacted.support_results.v20dc])

    self.reduced.hle_mac |= count_elements([x.evse_mac for x in self.compacted.slac_ids])
    self.reduced.phy_mac |= count_elements([x.mac for x in self.compacted.hpgp])
    self.reduced.phy_chip |= count_elements([x.ident for x in self.compacted.hpgp])
    self.reduced.phy_fw |= count_elements([x.version for x in self.compacted.hpgp])
    self.reduced.phy_mfg |= count_elements([x.mfg for x in self.compacted.hpgp])
    self.reduced.phy_usr |= count_elements([x.usr for x in self.compacted.hpgp])

def calculate_final(self: types.Plug):
    if self.reduced is None:
        raise ValueError()
    
    self.final = types.FinalResult(
        experiments= self.reduced.experiments,
        computed=True,

        nmk_random = verdict_int(self.reduced.nmk_random),
        nid_match = verdict_bool(self.reduced.nid_match),

        tls_support= verdict_bool(self.reduced.tls_support),
        tls_support_v13= verdict_bool(self.reduced.tls_support_v13),
        tls_support_v12= verdict_bool(self.reduced.tls_support_v12),
        tls_support_strong= verdict_bool(self.reduced.tls_support_strong),
        tls_support_weak= verdict_bool(self.reduced.tls_support_weak),
        tls_support_old= verdict_bool(self.reduced.tls_support_old),

        preferred = vertict_val(self.reduced.preferred),
        din_support= verdict_bool(self.reduced.din_support),
        v2v10_support= verdict_bool(self.reduced.v2v10_support),
        v2v13_support= verdict_bool(self.reduced.v2v13_support),
        v20dc_support= verdict_bool(self.reduced.v20dc_support),

        hle_mac= vertict_val(self.reduced.hle_mac),
        phy_mac= vertict_val(self.reduced.phy_mac),
        phy_chip= vertict_val(self.reduced.phy_chip),
        phy_fw= vertict_val(self.reduced.phy_fw),
        phy_mfg= vertict_val(self.reduced.phy_mfg),
        phy_usr= vertict_val(self.reduced.phy_usr),
    )
    self.final_sync_with_disk = False

    if self.final.tls_support == 0:
        self.final.tls_support_v13 = 0
        self.final.tls_support_v12 = 0
        self.final.tls_support_strong = 0
        self.final.tls_support_weak = 0
        self.final.tls_support_old = 0

def load_plug(plug: types.Plug) -> bool:
    res = False
    stat_file_path = os.path.join(plug.get_path(), "overview.json")
    if os.path.isfile(stat_file_path):
        with open(stat_file_path, "r") as f:
            plug.final = types.FinalResult.from_json(json.load(f))
            plug.final_sync_with_disk = True
        res = True
    return res

def process_plug(plug: types.Plug, run_policy: int) -> bool:
    load_data.read_plug_experiments(plug)

    if plug.experiments is not None and len(plug.experiments) > 0:
        print(f"Processing {plug.id}")
        for exp in plug.experiments:
            load_or_process_experiment(plug, exp, run_policy)
            
        review_plug_nmk(plug)

        for exp in plug.experiments:
            if not exp.results.disk_synced:
                save_experiment(exp)

        compact_results(plug)

        exp_times: List[datetime.datetime] = [
            datetime.datetime.strptime(exp.time[:19], "%Y-%m-%d %H:%M:%S") #type:ignore
        for exp in plug.experiments]
        
        exp_times = sorted(exp_times)
        exp_times_filter_last: datetime.datetime | None = None
        exp_times_filter = []
        for t in exp_times:
            if (exp_times_filter_last is None) or (t > (exp_times_filter_last + datetime.timedelta(hours=4))):
                exp_times_filter.append(datetime.datetime.strftime(t, "%Y-%m-%d %H:%M:%S"))
            exp_times_filter_last = t

        calculate_stats(plug, exp_times_filter)
        calculate_final(plug)

        return True
    else:
        print(f"Could not process {plug.id}, no data")
    return False

#0: Load only, 1: Load then run, 2: Run plug (load experiments then run) then load, 3: Run plug (Run experiments then load experiments) then load
def load_or_process_plug(plug: types.Plug, run_policy: int):
    #Must run fresh
    if run_policy >= 2:
        if process_plug(plug, run_policy):
            return True
    #Try load
    if load_plug(plug):
        return True
    #Allowed to run
    if run_policy == 1:
        if process_plug(plug, run_policy):
            return True
    
    plug.final = types.FinalResult()
    plug.final_sync_with_disk = False
    
def save_plug(plug: types.Plug):
    if plug.final is None:  
        return

    processed_file_path = os.path.join(plug.get_path(), "overview.json")
    os.makedirs(os.path.dirname(processed_file_path), exist_ok=True)
    with open(processed_file_path, "w") as f:
        json.dump(plug.final.to_json(), f, indent = 2)

def compute_stats(plugs: List[types.Plug]):

    all_breakdowns: List[str] = ["2013", "2014", "2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "????", "ALL"]

    def gen_entry() -> dict[str, dict[int, int]]:
        return {k: {0: 0, 1: 0, 2: 0} for k in all_breakdowns}

    all_stats: dict[str, dict[str, dict[int, int]]] = {
        "TLS_SDP": gen_entry(),

        "TLS_V20": gen_entry(),
        "TLS_V2": gen_entry(),
        "TLS_Strong": gen_entry(),
        "TLS_Weak": gen_entry(),
        "TLS_Old": gen_entry(),

        "V20DC": gen_entry(),
        "V2V13": gen_entry(),
        "V2V10": gen_entry(),
        "DIN": gen_entry(),
    }

    def count_stat(type: str, year: int | None, val: int):
        if val != -1:
            all_stats[type][str(year) if year is not None else "????"][val] += 1
            all_stats[type]["ALL"][val] += 1

    for plug in plugs:
        if plug.final is None:
            continue

        count_stat("TLS_SDP", plug.charger.mfg_year, plug.final.tls_support)

        count_stat("TLS_V20", plug.charger.mfg_year, plug.final.tls_support_v13)
        count_stat("TLS_V2", plug.charger.mfg_year, plug.final.tls_support_v12)
        count_stat("TLS_Strong", plug.charger.mfg_year, plug.final.tls_support_strong)
        count_stat("TLS_Weak", plug.charger.mfg_year, plug.final.tls_support_weak)
        count_stat("TLS_Old", plug.charger.mfg_year, plug.final.tls_support_old)

        count_stat("V20DC", plug.charger.mfg_year, plug.final.v20dc_support)
        count_stat("V2V13", plug.charger.mfg_year, plug.final.v2v13_support)
        count_stat("V2V10", plug.charger.mfg_year, plug.final.v2v10_support)
        count_stat("DIN", plug.charger.mfg_year, plug.final.din_support)

    def format_entry(entry: dict[int, int]):
        return f"{entry[2] + entry[1]} / {entry[0]}"

    full_table = [[""] + all_breakdowns] + [[k] + [format_entry(vv) for vv in v.values()] for k, v in all_stats.items()]

    folder = os.path.join(path_tools.REPO_BASE_DIR, "output")
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, "tls.csv"), "w") as f:
        for line in full_table:
            f.write(", ".join(line))
            f.write("\n")

    #print(tls_stats)
    return all_stats, all_breakdowns

    
if __name__ == "__main__":
    meta = metadata.read_charger_metadata_table()

    for plug in meta.plugs.values():
        load_or_process_plug(plug, 1)

    for plug in meta.plugs.values():
        if not plug.final_sync_with_disk:
            save_plug(plug)

    compute_stats(list(meta.plugs.values()))
