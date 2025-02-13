from __future__ import annotations

import json
import subprocess
import os
from quart import Quart, send_from_directory, request, jsonify, redirect, abort, render_template, send_file
import logging
import asyncio

from .. import process_data

from .. import path_tools
from .. import types
from .. import metadata
from . import page_gen
from . import static

logging.basicConfig()

process: None | subprocess.Popen = None

async def main_webserver(meta: metadata.Metadata):
    app = Quart(__name__)

    # Route for serving static files
    @app.route('/static/', defaults={'path': ''})
    @app.route('/static/<path>')
    async def serve_static_hander(path):
        return await static.serve_static_file_only(
            path,
            os.path.join(os.path.dirname(os.path.realpath(__file__)),"www"),
            False
        )
    
    @app.route('/photos/', defaults={'path': ''})
    @app.route('/photos/<path:path>')
    async def serve_photos_hander(path):
        return await static.serve_static_file_only(
            path,
            path_tools.PHOTOS_DIR,
            False
        )

    @app.route('/page/<park>.html')
    async def serve_data_pages(park):
        if park in meta.parks:

            global_js = []
            new_elem = page_gen.create_park_entry(meta.parks[park], request.query_string.decode() == "edit", global_js)

            js_string = json.dumps(''.join(global_js)).replace("<", "\\u003c")

            return page_gen.create_page(
                park,
                "../",
                new_elem + f"<script>eval({js_string})</script>"
            )
        else:
            return abort(404)

    @app.route('/api/edit/park/<park>', methods=['POST'])
    async def receive_data_park(park: str):
        data = await request.get_json()
        obj = meta.parks[park]
        obj.country = data["country"]
        obj.town = data["town"]
        obj.type = data["type"]
        obj.type2 = data["type2"]
        obj.lat = float(data["lat"])
        obj.long = float(data["long"])
        obj.notes = data["notes"]

        global_js = []
        new_elem = page_gen.create_park_table_info(obj, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}
    
    @app.route('/api/edit/charger/<charger>', methods=['POST'])
    async def receive_data_charger(charger: str):
        data = await request.get_json()
        obj = meta.chargers[charger]
        obj.position = data["position"]
        obj.manufacturer = data["manufacturer"]
        obj.network = data["network"]
        obj.model = data["model"]
        obj.mfg_year = int(data["mfg_year"]) if len(data["mfg_year"]) else None
        obj.mfg_detail = data["mfg_detail"]
        obj.sn = data["sn"]
        obj.notes = data["notes"]

        global_js = []
        new_elem = page_gen.create_charger_table_info(obj, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}
    
    @app.route('/api/edit/plug/<plug>', methods=['POST'])
    async def receive_data_plug(plug: str):
        data = await request.get_json()
        obj = meta.plugs[plug]
        obj.position = data["position"]
        obj.notes = data["notes"]

        global_js = []
        new_elem = page_gen.create_plug_table_info(obj, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}
    
    @app.route('/api/new/park/<park>', methods=['POST'])
    async def create_new_park(park: str):
        if park in meta.parks:
            return {"status": "Already exists"}
        res = types.Park(
            id = park,
            country = "",
            town = "",
            type = "",
            type2 = "",
            lat = 0,
            long = 0,
            photos = "",
            notes = "",

            chargers = []
        )
        meta.parks[park] = res

        global_js = []
        new_elem = page_gen.create_park_entry(res, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}
    
    @app.route('/api/new/charger/<charger>', methods=['POST'])
    async def create_new_charger(charger: str):
        if charger in meta.chargers:
            return {"status": "Already exists"}
        park_id = charger.rsplit(".", maxsplit=1)[0]
        if park_id not in meta.parks:
            return {"status": "Parent does not exist"}
        park = meta.parks[park_id]
        res = types.Charger(
            park = park,
            id = charger,
            position = "",
            manufacturer = "",
            network = "",
            model = "",
            mfg_year = None,
            mfg_detail = "",
            sn = "",
            photos = "",
            notes = "",
            
            plugs = []
        )
        meta.chargers[charger] = res
        park.chargers.append(res)

        global_js = []
        new_elem = page_gen.create_charger_entry(res, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}
    
    @app.route('/api/new/plug/<plug>', methods=['POST'])
    async def create_new_plug(plug):
        if plug in meta.plugs:
            return {"status": "Already exists"}
        charger_id = plug.rsplit(".", maxsplit=1)[0]
        if charger_id not in meta.chargers:
            return {"status": "Parent does not exist"}
        charger = meta.chargers[charger_id]
        res = types.Plug(
            charger = charger,
            id = plug,
            position = "",
            notes = "",
            experiments = None,
            compacted = None,
            reduced= None,
            final = None,
            final_sync_with_disk = False,
        )
        res.final = types.FinalResult()
        meta.plugs[plug] = res
        charger.plugs.append(res)

        global_js = []
        new_elem = page_gen.create_plug_entry(res, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}
        
    @app.route('/api/edit/result/<plug>', methods=['POST'])
    async def receive_data_result(plug: str):
        data = await request.get_json()
        obj = meta.plugs[plug]
        if obj.final is None:
             obj.final = types.FinalResult()
        obj.final.computed = False
        obj.final.nmk_random = int(data["nmk_random"])
        obj.final.nid_match = int(data["nid_match"])

        obj.final.tls_support = int(data["tls_support"])
        obj.final.tls_support_v13 = int(data["tls_support_v13"])
        obj.final.tls_support_v12 = int(data["tls_support_v12"])
        obj.final.tls_support_strong = int(data["tls_support_strong"])
        obj.final.tls_support_weak = int(data["tls_support_weak"])
        obj.final.tls_support_old = int(data["tls_support_old"])

        obj.final.preferred = data["preferred"]
        obj.final.din_support = int(data["din_support"])
        obj.final.v2v10_support = int(data["v2v10_support"])
        obj.final.v2v13_support = int(data["v2v13_support"])
        obj.final.v20dc_support = int(data["v20dc_support"])

        obj.final.hle_mac = data["hle_mac"]
        obj.final.phy_mac = data["phy_mac"]
        obj.final.phy_chip = data["phy_chip"]
        obj.final.phy_fw = data["phy_fw"]
        obj.final.phy_mac = data["phy_mac"]
        obj.final.phy_mfg = data["phy_mfg"]
        obj.final.phy_usr = data["phy_usr"]
        
        global_js = []
        new_elem = page_gen.create_plug_table_results(obj, True, global_js)
        return {"ok": True, "status": "OK", "elem": new_elem, "code": global_js}

    @app.route('/')
    @app.route('/index.html')
    async def handle_root():
        page_content = "".join([page_gen.create_plug_table_row(plug, request.query_string.decode() == "edit") for plug in meta.plugs.values()])
        return page_gen.create_page("List","", f"<table class=\"result_table\">{page_gen.create_plug_table_header()}{page_content}</table>")
    


    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    # Generate with Lets Encrypt, copied to this location, chown to current user and 400 permissions
    #ssl_cert = os.path.join(os.path.dirname(os.path.realpath(__file__)),"www/certs/certificate.pem")
    #ssl_key = os.path.join(os.path.dirname(os.path.realpath(__file__)),"www/certs/key.pem")

    await app.run_task(host="0.0.0.0", port=8000)#, certfile=ssl_cert, keyfile=ssl_key)


async def main():
    meta =  metadata.read_charger_metadata_table()
    for plug in meta.plugs.values():
        process_data.load_or_process_plug(plug, 1)
    try:
        await main_webserver(meta)
    finally:
        metadata.save_charger_metadata_table(meta)
        for plug in meta.plugs.values():
            if not plug.final_sync_with_disk:
                process_data.save_plug(plug)

def syncmain():
    asyncio.run(main())

if __name__ == '__main__':
    syncmain()