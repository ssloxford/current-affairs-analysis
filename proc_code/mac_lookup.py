"""
Utilities for MAC addresses, includes a list of for OUI manufacturer lookup.
"""

from typing import Dict, List

from . import utils

lut = {
    "00005E"    :"ICANN, IANA Department",
    "000187"    :"I2SE GmbH",
    "001395"    :"congatec GmbH",
    "001EC0"    :"Microchip Technology Inc.",
    "006037"    :"NXP Semiconductors",
    "00B052"    :"Atheros Communications",
    "049162"    :"Microchip Technology Inc.",
    "141FBA1"   :"GloQuad",
    "18D793B"   :"EcoG",
    "5410EC"    :"Microchip Technology Inc.",
    "60FAB1"    :"Kempower Oyj",
    "682719"    :"Microchip Technology Inc.",
    "7050E75"   :"Wall Box Chargers, S.L.",
    "70B3D5D41" :"KSE GmbH",
    "801F12"    :"Microchip Technology Inc.",
    "803428"    :"Microchip Technology Inc.",
    "8C34FD"    :"Huawei Technologies Co.,Ltd",
    "D88039"    :"Microchip Technology Inc.",
    "DC44271"   :"Tesla,Inc.",
    "E41E0A7"   :"Tritium Pty Ltd",
    "E8EB1B"    :"Microchip Technology Inc.",
}

#Remove non OUI. If can't find, truncate to OUI region
def redact_mac(m: str) -> str:
    m = m.replace(":", "").upper()
    found = False
    for k, v in lut.items():
        if m.startswith(k):
            return k + ("X" * (12 - len(k)))
    return m[:6] + ("XXXXXXXXXXXX"[6:len(m)])

def format_mac(m: str) -> str:
    m = m.replace(":", "").upper()

    return ":".join(m[i:i+2] for i in range(6))

# Returns sorted dictionary name->count
def mac_oui_lookup(macs: List[str]) -> Dict[str, int]:
    nets: List[str] = []
    for m in macs:
        if len(m) < 2:
            continue
        m = m.replace(":", "").upper()
        found = False
        for k, v in lut.items():
            if m.startswith(k):
                nets.append(v)
                found = True
        if not found:
            if "26AE".find(m[1]) != -1:
                nets.append("Locally Administered")
            else:
                # Check the OUI list for new entries. https://www.wireshark.org/tools/oui-lookup.html
                print(m)
                nets.append("Unknown")

    nets_dict = utils.count_elements(nets)
    sorted_dict = {k:nets_dict[k] for _,k in sorted([(kk.lower(),kk) for kk in nets_dict.keys()])}

    return sorted_dict