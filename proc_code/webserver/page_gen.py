from __future__ import annotations

import base64
from dataclasses import dataclass
import html
import json
import os
from typing import Any, Dict, Iterable, List, Tuple

from .. import path_tools

from .. import types

#
# MAP
#

def decimal_to_dms(lat, lon):
    # Function to convert decimal degrees to DMS format
    def convert_to_dms(degrees):
        d = int(degrees)
        minutes = (degrees - d) * 60
        m = int(minutes)
        seconds = (minutes - m) * 60
        s = round(seconds, 1)  # Round to one decimal place
        return d, m, s

    # Convert latitude
    lat_d, lat_m, lat_s = convert_to_dms(abs(lat))
    lat_direction = 'N' if lat >= 0 else 'S'
    
    # Convert longitude
    lon_d, lon_m, lon_s = convert_to_dms(abs(lon))
    lon_direction = 'E' if lon >= 0 else 'W'
    
    # Format the output
    lat_dms = f"{lat_d}°{lat_m}'{lat_s}\"{lat_direction}"
    lon_dms = f"{lon_d}°{lon_m}'{lon_s}\"{lon_direction}"
    
    return f"{lat_dms} {lon_dms}"

def create_gmaps_iframe(lat: float, long: float, distance=1000):    
    url = f"https://www.google.com/maps/embed?pb=!1m17!1m12!1m3!1d{distance}!2d{long}!3d{lat}!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m2!1m1!2z{base64.b64encode(decimal_to_dms(lat, long).encode()).decode().rstrip('=')}!5e1!3m2!1sen!2suk!4v1736791101121!5m2!1sen!2suk"
    return f"<iframe width=\"600\" height=\"450\" style=\"border:0;\" allowfullscreen=\"\" loading=\"lazy\" referrerpolicy=\"no-referrer-when-downgrade\" src=\"{url}\"></iframe>"

#
# Editing UI
#

class SaveCall():
    location: str
    args: Dict[str, str]

    def __init__(self, location):
        self.location = location
        self.args = {}
        self.root_id = get_uid()

    def add(self, name: str):
        return lambda idx: self.args.__setitem__(name, idx)

uid_counter = 0
uid_global = os.urandom(8).hex()
def get_uid():
    global uid_counter
    global uid_global
    uid_counter += 1
    return f"elem_{uid_global}_{uid_counter}"

#
# Create elements
#

RESULT_LUT = {-1: "—", 0: "❌",1: "❔",2: "✅"}
RESULT_NMK_LUT = {-1: "—", 0: "❌",1: "~",2: "✅"}
RESULT_PREFERRED_LUT = {"": "?", "DIN":"DIN", "V2V10": "ISO 15118-2:2010", "V2V13": "ISO 15118-2:2013", "V20DC": "ISO 15118-20 DC"}

def create_collapsable_list(name: str, elems: List[str]):
    return f"<details class=\"dropdown\" open><summary class=\"dropdown_hdr\">{html.escape(name)}</summary><div class=\"dropdown_content\">{''.join(elems)}</div></details>"

def create_str_field(content: str, api, edit: bool, args={}):
    if edit:
        id = get_uid()
        api(id)
        edit_params = ' '.join([f"{k}=\"{html.escape(v, quote=True)}\"" for k, v in args.items()])
        return f"<input {edit_params} id=\"{html.escape(id, quote=True)}\" value=\"{html.escape(content, quote=True)}\">"
    else:
        return f"<span>{html.escape(content)}</span>"

def create_select_field(content: Any, api, edit: bool, options: Dict[Any, str], args={}):
    if edit:
        id = get_uid()
        api(id)
        edit_params = ' '.join([f"{k}=\"{html.escape(v, quote=True)}\"" for k, v in args.items()])
        options_str="".join([f"<option value=\"{html.escape(str(k), quote=True)}\" {'selected' if k == content else ''}>{html.escape(v)}</option>" for k, v in options.items()])
        return f"<select {edit_params} id=\"{html.escape(id, quote=True)}\">\
            {options_str}</select>"
    else:
        return f"<span>{html.escape(options[content if content in options else ''])}</span>"


def create_int_field(content: int | None, api, edit: bool):
    return create_str_field(str(content) if content is not None else "", api, edit, {"type": "number", "step": "1"})

def create_float_field(content: float | None, api, edit: bool):
    return create_str_field(str(content) if content is not None else "", api, edit, {"type": "number", "step": "any"})

def create_result_field(content: int, api, edit: bool, lut = RESULT_LUT):
    return create_select_field(content, api, edit, lut, {})


def create_kv_pair(k: str, vh: str):
    return f"<tr><td>{html.escape(k)}</td><td>{vh}</td></tr>"

def create_image(src: str):
    return f"<image height=200 src=\"{html.escape(src, quote=True)}\">"

def create_photo(fn: str):
    return create_image('../photos/'  + path_tools.get_photo_dir(fn))

def create_photo_list(fns: Iterable[str]):
    content = ''.join([create_photo(fn) for fn in fns])
    return f"<div class=\"imagelist\">{content}</div>"

def create_datalist(id: str, entries: List[str]):
    entries_str = "".join([f"<option value=\"{html.escape(entry, quote=True)}\"></option>" for entry in entries])
    return f"<datalist id=\"{html.escape(id, quote=True)}\">{entries_str}</datalist>"

def create_page(title: str, toroot: str, content: str):
    return f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\">\
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\
    <script type=\"text/javascript\" src=\"{html.escape(toroot, quote=True)}static/index.js\"></script>\
    <link rel=\"icon\" href=\"data:;base64,=\">\
    <title>{html.escape(title)}</title>\
    <link rel=\"stylesheet\" href=\"{html.escape(toroot, quote=True)}static/index.css\">\
    </head><body>{content}</body></html>"

def create_api_button(text: str, api: SaveCall, edit: bool, global_js: List[str]) -> str:
    if not edit:
        return ""
    button_uid = get_uid()
    global_js.append(f"create_api_form({json.dumps(api.location)}, {json.dumps(api.args)}, {json.dumps(api.root_id)}, {json.dumps(button_uid)});")
    return f"<button id=\"{html.escape(button_uid, quote=True)}\">{html.escape(text)}</button><br/>"

def create_add_new_button(type: str, prefix: str):
    return f"<button onclick=\"api_call_create('../api/new', '{html.escape(type, quote=True)}', '{html.escape(prefix, quote=True)}', this)\">New {html.escape(type)}</button>"

#
# Main page
#

def create_plug_table_header():
    return f"<tr>\
    <th>ID</th>\
    <th>Town</th>\
    <th>Manufacturer</th>\
    <th>Operator</th>\
    <th>Model</th>\
    <th>TLS</th>\
    <th>DIN</th>\
    <th>15118-2</th>\
    <th>Preferred</th>\
    </tr>"

def create_plug_table_row(plug: types.Plug, edit: bool):
    return f"<tr>\
    <td><a href=\"page/{html.escape(plug.charger.park.id + '.html' + ('?edit' if edit else ''),quote=True)}\">{html.escape(plug.id)}</a></td>\
    <td>{html.escape(plug.charger.park.town)}</td>\
    <td>{html.escape(plug.charger.manufacturer)}</td>\
    <td>{html.escape(plug.charger.network)}</td>\
    <td>{html.escape(plug.charger.model)}</td>\
    <td>{RESULT_LUT[plug.final.tls_support if plug.final is not None else -1]}</td>\
    <td>{RESULT_LUT[plug.final.din_support if plug.final is not None else -1]}</td>\
    <td>{RESULT_LUT[plug.final.v2v13_support if plug.final is not None else -1]}</td>\
    <td>{plug.final.preferred if plug.final is not None else RESULT_LUT[-1]}</td>\
    </tr>"

#
# Create page for components
#

def create_plug_table_info(plug: types.Plug, edit: bool, global_js: List[str]) -> str:
    api = SaveCall(f"../api/edit/plug/{plug.id}")

    table = f"<table> \
        {create_kv_pair('Position', create_str_field(plug.position, api.add('position'), edit))} \
        {create_kv_pair('Notes', create_str_field(plug.notes, api.add('notes'), edit))} \
        </table>"

    return f"<div id=\"{html.escape(api.root_id, quote=True)}\">{table}{create_api_button('Save Changes', api, edit, global_js)}</div>"
        

def create_plug_table_results(plug: types.Plug, edit: bool, global_js: List[str]) -> str:
    if plug.final is None:
        raise ValueError("No results")

    api = SaveCall(f"../api/edit/result/{plug.id}")

    times = "</br>".join([f"<span>{e} UTC</span>" for e in plug.final.experiments])

    table = f"<div>Experiment times:</br>{times}</div><table> \
        {create_kv_pair('nmk_random', create_result_field(plug.final.nmk_random, api.add('nmk_random'), edit, RESULT_NMK_LUT))} \
        {create_kv_pair('nid_match', create_result_field(plug.final.nid_match, api.add('nid_match'), edit))} \
        \
        {create_kv_pair('tls_support', create_result_field(plug.final.tls_support, api.add('tls_support'), edit))} \
        {create_kv_pair('tls_support_v13', create_result_field(plug.final.tls_support_v13, api.add('tls_support_v13'), edit))} \
        {create_kv_pair('tls_support_v12', create_result_field(plug.final.tls_support_v12, api.add('tls_support_v12'), edit))} \
        {create_kv_pair('tls_support_strong', create_result_field(plug.final.tls_support_strong, api.add('tls_support_strong'), edit))} \
        {create_kv_pair('tls_support_weak', create_result_field(plug.final.tls_support_weak, api.add('tls_support_weak'), edit))} \
        {create_kv_pair('tls_support_old', create_result_field(plug.final.tls_support_old, api.add('tls_support_old'), edit))} \
        \
        {create_kv_pair('preferred', create_select_field(plug.final.preferred, api.add('preferred'), edit, RESULT_PREFERRED_LUT))} \
        {create_kv_pair('din_support', create_result_field(plug.final.din_support, api.add('din_support'), edit))} \
        {create_kv_pair('v2v10_support', create_result_field(plug.final.v2v10_support, api.add('v2v10_support'), edit))} \
        {create_kv_pair('v2v13_support', create_result_field(plug.final.v2v13_support, api.add('v2v13_support'), edit))} \
        {create_kv_pair('v20dc_support', create_result_field(plug.final.v20dc_support, api.add('v20dc_support'), edit))} \
        \
        {create_kv_pair('hle_mac', create_str_field(plug.final.hle_mac, api.add('hle_mac'), edit))} \
        {create_kv_pair('phy_mac', create_str_field(plug.final.phy_mac, api.add('phy_mac'), edit))} \
        {create_kv_pair('phy_chip', create_str_field(plug.final.phy_chip, api.add('phy_chip'), edit))} \
        {create_kv_pair('phy_fw', create_str_field(plug.final.phy_fw, api.add('phy_fw'), edit))} \
        {create_kv_pair('phy_mfg', create_str_field(plug.final.phy_mfg, api.add('phy_mfg'), edit))} \
        {create_kv_pair('phy_usr', create_str_field(plug.final.phy_usr, api.add('phy_usr'), edit))} \
        </table>"

    return f"<div id=\"{html.escape(api.root_id, quote=True)}\">{table}{create_api_button('Save Changes', api, edit, global_js)}</div>"

def create_plug_entry(plug: types.Plug, edit: bool, global_js: List[str]):
    return (
    f"<div class='plug'>\
        <div class='id' id=\"{html.escape(plug.id, quote=True)}\">{html.escape(plug.id)}</div>\
        {create_plug_table_info(plug, edit, global_js)}\
        </br>\
        {create_plug_table_results(plug, edit and (plug.final is None or not plug.final.computed), global_js)}\
    </div>")



def create_charger_table_info(charger: types.Charger, edit: bool, global_js: List[str]) -> str:
    api = SaveCall(f"../api/edit/charger/{charger.id}")
 
    table = f"<table> \
        {create_kv_pair('Position', create_str_field(charger.position, api.add('position'), edit))} \
        {create_kv_pair('Manufacturer', create_str_field(charger.manufacturer, api.add('manufacturer'), edit))} \
        {create_kv_pair('Operator', create_str_field(charger.network, api.add('network'), edit))} \
        {create_kv_pair('Model', create_str_field(charger.model, api.add('model'), edit))} \
        {create_kv_pair('Date year', create_int_field(charger.mfg_year, api.add('mfg_year'), edit))} \
        {create_kv_pair('Date extra', create_str_field(charger.mfg_detail, api.add('mfg_detail'), edit))} \
        {create_kv_pair('Serial', create_str_field(charger.sn, api.add('sn'), edit))} \
        {create_kv_pair('Notes', create_str_field(charger.notes, api.add('notes'), edit))} \
        </table>"
    
    return f"<div id=\"{html.escape(api.root_id, quote=True)}\">{table}{create_api_button('Save Changes', api, edit, global_js)}</div>"
        

def create_charger_entry(charger: types.Charger, edit: bool, global_js: List[str]):
    return (
    f"<div class='charger'>\
        <div class='id' id=\"{html.escape(charger.id, quote=True)}\">{html.escape(charger.id)}</div>\
        {create_photo_list(charger.get_photos())} \
        {create_charger_table_info(charger, edit, global_js)}\
        {create_collapsable_list('Plugs', [create_plug_entry(p, edit, global_js) for p in charger.plugs] + [create_add_new_button('plug', charger.id + '.') for _ in range(1 if edit else 0)])} \
    </div>")


def create_park_table_info(park: types.Park, edit: bool, global_js: List[str]) -> str:
    api = SaveCall(f"../api/edit/park/{park.id}")
 
    table = f"<table>\
        {create_kv_pair('Country', create_str_field(park.country, api.add('country'), edit))} \
        {create_kv_pair('Town', create_str_field(park.town, api.add('town'), edit))} \
        {create_kv_pair('Type', create_str_field(park.type, api.add('type'), edit))} \
        {create_kv_pair('Type2', create_str_field(park.type2, api.add('type2'), edit))} \
        {create_kv_pair('Lat', create_float_field(park.lat, api.add('lat'), edit))} \
        {create_kv_pair('Long', create_float_field(park.long, api.add('long'), edit))} \
        {create_kv_pair('Notes', create_str_field(park.notes, api.add('notes'), edit))} \
        </table>"

    return f"<div id=\"{html.escape(api.root_id, quote=True)}\">{table}{create_api_button('Save Changes', api, edit, global_js)}</div>"

def create_park_entry(park: types.Park, edit: bool, global_js: List[str]) -> str:
    return (
    f"<div class='charger'>\
        <div class='id' id=\"{html.escape(park.id, quote=True)}\">{html.escape(park.id)}</div>\
        {create_gmaps_iframe(park.lat, park.long)} \
        {create_photo_list(park.get_photos())} \
        {create_park_table_info(park, edit, global_js)}\
        {create_collapsable_list('Chargers', [create_charger_entry(c, edit, global_js) for c in park.chargers] + [create_add_new_button('charger', park.id + '.') for _ in range(1 if edit else 0)])} \
    </div>")