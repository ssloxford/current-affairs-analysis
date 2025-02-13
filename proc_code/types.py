from __future__ import annotations
import dataclasses
import os
from typing import List, TypeVar, Dict

from dataclasses import dataclass
from typing import Dict, List, NamedTuple

from . import path_tools

from .utils import parse_float, parse_int, count_elements, verdict_bool, verdict_int, vertict_val

@dataclass
class Park:
    id: str
    country: str
    town: str
    type: str
    type2: str
    lat: float
    long: float
    photos: str
    notes: str

    chargers: List[Charger]

    @staticmethod
    def create(x):
        return Park(
            x["ID"],
            x["Country"], x["Town"],
            x["Type"], x["Type2"],
            parse_float(x["Lat"]), parse_float(x["Long"]),
            x["Photos"], x["Notes"], []
        )

    def get_photos(self):
        return filter(lambda f: len(f) > 0, [p.strip().rstrip() for p in self.photos.split(',')])

@dataclass
class Charger:
    park: Park
    id: str
    position: str
    manufacturer: str
    network: str
    model: str
    mfg_year: int | None
    mfg_detail: str
    sn: str
    photos: str
    notes: str

    plugs: List[Plug]

    @staticmethod
    def create(x, parks: Dict[str, Park]):
        park = parks[x["ID"].rsplit(".", 1)[0]]
        res = Charger(
            park,
            x["ID"],
            x["Position"],
            x["Manufacturer"], x["Operator"], x["Model"],
            parse_int(x["MFGYear"]), x["MFGDetail"],
            x["SN"],
            x["Photos"], x["Notes"], []
        )
        park.chargers.append(res)
        return res
    
    def get_photos(self):
        return filter(lambda f: len(f) > 0, [p.strip().rstrip() for p in self.photos.split(',')])

@dataclass
class Plug:
    charger: Charger
    id: str
    position: str
    notes: str

    experiments: List[Experiment] | None
    compacted: ExperimentResult | None
    reduced: ReducedResult | None
    final: FinalResult | None
    final_sync_with_disk: bool

    @staticmethod
    def create(x, chargers: Dict[str, Charger]):
        charger = chargers[x["ID"].rsplit(".", 1)[0]]
        res = Plug(
            charger = charger,
            id = x["ID"],
            position = x["Position"],
            notes = x["Notes"],
            experiments = None,
            compacted = None,
            reduced= None,
            final = None,
            final_sync_with_disk = False,
        )
        charger.plugs.append(res)
        return res



    def get_folder(self):
        return path_tools.get_plug_folder(self.id)

    def get_path(self):
        return path_tools.get_plug_path(self.id)
    
@dataclass
class Experiment:
    path: str
    version: int | None
    time: str | None

    results: ExperimentResult

    #def to_json(self):
    #    return {
    #        "path": self.path,
    #        "version": self.version,
    #        
    #        "results": self.results,
    #    }

@dataclass
class SlacNMKResult:
    nmk: str
    nid: str
    nid_match: bool
    random: int | None

    def to_json(self):
        return {
            "nmk": self.nmk,
            "nid": self.nid,
            "nid_match": self.nid_match,
            "random": self.random,
        }
    
    @staticmethod
    def from_json(j):
        return SlacNMKResult(
            nmk = j["nmk"],
            nid = j["nid"],
            nid_match = j["nid_match"],
            random = j["random"],
        )

class SlacSoundingResult(NamedTuple):
    evse_mac: str
    evse_id: str
    aag: str

    def to_json(self):
        return {
            "evse_mac": self.evse_mac,
            "evse_id": self.evse_id,
            "aag": self.aag,
        }
    
    @staticmethod
    def from_json(j):
        return SlacSoundingResult(
            evse_mac = j["evse_mac"],
            evse_id = j["evse_id"],
            aag = j["aag"]
        )

class SDPResult(NamedTuple):
    req_tls: bool

    res_tls: bool
    port: int

    def to_json(self):
        return {
            "req_tls": self.req_tls,
            "res_tls": self.res_tls,
            "port": self.port,
        }
    
    @staticmethod
    def from_json(j):
        return SDPResult(
            req_tls = j["req_tls"],
            res_tls = j["res_tls"],
            port = j["port"]
        )

class HPGPCCoResult(NamedTuple):
    mac: str

    ident: str
    version: str

    mfg: str
    usr: str

    def to_json(self):
        return {
            "mac": self.mac,
            "ident": self.ident,
            "version": self.version,
            "mfg": self.mfg,
            "usr": self.usr,
        }
    
    @staticmethod
    def from_json(j):
        return HPGPCCoResult(
            mac = j["mac"],
            ident = j["ident"],
            version = j["version"],
            mfg = j["mfg"],
            usr = j["usr"]
        )

@dataclass
class SupportedResult():
    preferred: List[str]

    din: List[str]
    v2v10: List[str]
    v2v13: List[str]
    v20dc: List[str]

    def __init__(self):
        self.preferred = []

        self.din = []
        self.v2v10 = []
        self.v2v13 = []
        self.v20dc = []

    def to_json(self):
        return {
            "preferred": self.preferred,
            "din": self.din,
            "v2v10": self.v2v10,
            "v2v13": self.v2v13,
            "v20dc": self.v20dc,
        }
    
    @staticmethod
    def from_json(j):
        res = SupportedResult()
        res.preferred = j["preferred"]
        res.din = j["din"]
        res.v2v10 = j["v2v10"]
        res.v2v13 = j["v2v13"]
        res.v20dc = j["v20dc"]
        return res

@dataclass
class TLSResult():
    v13: List[bool]
    v12: List[bool]
    strong: List[int]
    weak: List[int]
    old: List[bool]

    def __init__(self):
        self.v13 = []
        self.v12 = []
        self.strong = []
        self.weak = []
        self.old = []

    def to_json(self):
        return {
            "v13" : self.v13,
            "v12" : self.v12,
            "strong" : self.strong,
            "weak" : self.weak,
            "old" : self.old,
        }
    
    @staticmethod
    def from_json(j):
        res = TLSResult()
        res.v13 = j["v13"]
        res.v12 = j["v12"]
        res.strong = j["strong"]
        res.weak = j["weak"]
        res.old = j["old"]
        return res

@dataclass
class ExperimentResult:
    hpgp: List[HPGPCCoResult]

    slac_nmk: List[SlacNMKResult]
    slac_ids: List[SlacSoundingResult]

    sdp_results: List[SDPResult]

    tls_results: TLSResult

    support_results: SupportedResult

    disk_synced: bool

    def __init__(self):
        self.hpgp = []

        self.slac_nmk = []
        self.slac_ids = []

        self.sdp_results = []

        self.tls_results = TLSResult()

        self.support_results = SupportedResult()

        self.disk_synced = False

    def to_json(self):
        return {
            "hpgp": [x.to_json() for x in self.hpgp],
            "slac_nmk": [x.to_json() for x in self.slac_nmk],
            "slac_ids": [x.to_json() for x in self.slac_ids],
            "sdp_results": [x.to_json() for x in self.sdp_results],
            "tls_results": self.tls_results.to_json(),
            "support_results": self.support_results.to_json(),
        }
    
    def set_from_json(self, j):
        self.hpgp = [HPGPCCoResult.from_json(jj) for jj in j["hpgp"]]
        self.slac_nmk = [SlacNMKResult.from_json(jj) for jj in j["slac_nmk"]]
        self.slac_ids = [SlacSoundingResult.from_json(jj) for jj in j["slac_ids"]]
        self.sdp_results = [SDPResult.from_json(jj) for jj in j["sdp_results"]]
        self.tls_results = TLSResult.from_json(j["tls_results"])
        self.support_results = SupportedResult.from_json(j["support_results"])
        self.disk_synced = True
        
    @staticmethod
    def from_json(j):
        res = ExperimentResult()
        res.set_from_json(j)
        return res

@dataclass
class ReducedResult:
    experiments: List[str]

    nmk_random: Dict[int, int]
    nid_match: Dict[bool, int]

    tls_support: Dict[bool, int]
    tls_support_v13: Dict[bool, int]
    tls_support_v12: Dict[bool, int]
    tls_support_strong: Dict[bool, int]
    tls_support_weak: Dict[bool, int]
    tls_support_old: Dict[bool, int]

    preferred: Dict[str, int]
    din_support: Dict[bool, int]
    v2v10_support: Dict[bool, int]
    v2v13_support: Dict[bool, int]
    v20dc_support: Dict[bool, int]

    hle_mac: Dict[str, int]
    phy_mac: Dict[str, int]
    phy_chip: Dict[str, int]
    phy_fw: Dict[str, int]
    phy_mfg: Dict[str, int]
    phy_usr: Dict[str, int]

    def __init__(self):
        self.experiments = []

        self.nmk_random = {0: 0, 1: 0, 2: 0}
        self.nid_match = {False: 0, True: 0}

        self.tls_support = {False: 0, True: 0}
        self.tls_support_v13 = {False: 0, True: 0}
        self.tls_support_v12 = {False: 0, True: 0}
        self.tls_support_strong = {False: 0, True: 0}
        self.tls_support_weak = {False: 0, True: 0}
        self.tls_support_old = {False: 0, True: 0}

        self.preferred = {}
        self.din_support = {False: 0, True: 0}
        self.v2v10_support = {False: 0, True: 0}
        self.v2v13_support = {False: 0, True: 0}
        self.v20dc_support = {False: 0, True: 0}

        self.hle_mac = {}
        self.phy_mac = {}
        self.phy_chip = {}
        self.phy_fw = {}
        self.phy_mfg = {}
        self.phy_usr = {}

    def to_json(self):
        return {
            "experiments": self.experiments,

            "nmk_random": self.nmk_random,
            "nid_match": self.nid_match,

            "tls_support": self.tls_support,
            "tls_support_v13": self.tls_support_v13,
            "tls_support_v12": self.tls_support_v12,
            "tls_support_strong": self.tls_support_strong,
            "tls_support_weak": self.tls_support_weak,
            "tls_support_old": self.tls_support_old,


            "preferred": self.preferred,
            "din_support": self.din_support,
            "v2v10_support": self.v2v10_support,
            "v2v13_support": self.v2v13_support,
            "v20dc_support": self.v20dc_support,

            "hle_mac": self.hle_mac,
            "phy_mac": self.phy_mac,
            "phy_chip": self.phy_chip,
            "phy_fw": self.phy_fw,
            "phy_mfg": self.phy_mfg,
            "phy_usr": self.phy_usr,
        }

    @staticmethod
    def from_json(j):
        res = ReducedResult()
        res.experiments = j["experiments"]

        res.nmk_random = j["nmk_random"]
        res.nid_match = j["nid_match"]
        
        res.tls_support = j["tls_support"]
        res.tls_support_v13 = j["tls_support_v13"]
        res.tls_support_v12 = j["tls_support_v12"]
        res.tls_support_strong = j["tls_support_strong"]
        res.tls_support_weak = j["tls_support_weak"]
        res.tls_support_old = j["tls_support_old"]

        res.preferred = j["preferred"]
        res.din_support = j["din_support"]
        res.v2v10_support = j["v2v10_support"]
        res.v2v13_support = j["v2v13_support"]
        res.v20dc_support = j["v20dc_support"]

        res.hle_mac = j["hle_mac"]
        res.phy_mac = j["phy_mac"]
        res.phy_chip = j["phy_chip"]
        res.phy_fw = j["phy_fw"]
        res.phy_mfg = j["phy_mfg"]
        res.phy_usr = j["phy_usr"]

        return res

@dataclass
class FinalResult:
    experiments: List[str] = dataclasses.field(default_factory=lambda: [])
    computed: bool = False

    nmk_random: int = -1
    nid_match: int = -1

    tls_support: int = -1
    tls_support_v13: int = -1
    tls_support_v12: int = -1
    tls_support_strong: int = -1
    tls_support_weak: int = -1
    tls_support_old: int = -1

    preferred: str = ""
    din_support: int = -1
    v2v10_support: int = -1
    v2v13_support: int = -1
    v20dc_support: int = -1

    hle_mac: str = ""
    phy_mac: str = ""
    phy_chip: str = ""
    phy_fw: str = ""
    phy_mfg: str = ""
    phy_usr: str = ""

    def to_json(self):
        return {
            "experiments": self.experiments,
            "computed": self.computed,

            "nmk_random": self.nmk_random,
            "nid_match": self.nid_match,

            "tls_support": self.tls_support,
            "tls_support_v13": self.tls_support_v13,
            "tls_support_v12": self.tls_support_v12,
            "tls_support_strong": self.tls_support_strong,
            "tls_support_weak": self.tls_support_weak,
            "tls_support_old": self.tls_support_old,

            "preferred": self.preferred,
            "din_support": self.din_support,
            "v2v10_support": self.v2v10_support,
            "v2v13_support": self.v2v13_support,
            "v20dc_support": self.v20dc_support,

            "hle_mac": self.hle_mac,
            "phy_mac": self.phy_mac,
            "phy_chip": self.phy_chip,
            "phy_fw": self.phy_fw,
            "phy_mfg": self.phy_mfg,
            "phy_usr": self.phy_usr,
        }

    @staticmethod
    def from_json(j):
        return FinalResult(
            experiments = j["experiments"],
            computed = j["computed"],

            nmk_random = j["nmk_random"],
            nid_match = j["nid_match"],
            
            tls_support = j["tls_support"],
            tls_support_v13 = j["tls_support_v13"],
            tls_support_v12 = j["tls_support_v12"],
            tls_support_strong = j["tls_support_strong"],
            tls_support_weak = j["tls_support_weak"],
            tls_support_old = j["tls_support_old"],

            preferred = j["preferred"],
            din_support = j["din_support"],
            v2v10_support = j["v2v10_support"],
            v2v13_support = j["v2v13_support"],
            v20dc_support = j["v20dc_support"],

            hle_mac = j["hle_mac"],
            phy_mac = j["phy_mac"],
            phy_chip = j["phy_chip"],
            phy_fw = j["phy_fw"],
            phy_mfg = j["phy_mfg"],
            phy_usr = j["phy_usr"]
        )
