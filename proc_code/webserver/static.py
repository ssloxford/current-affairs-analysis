from __future__ import annotations

import os
from quart import Quart, send_from_directory, request, jsonify, redirect, abort, render_template, send_file

def in_directory(full_path, directory):
    #make both absolute    
    directory = os.path.join(os.path.realpath(directory), '')

    #return true, if the common prefix of both is equal to directory
    #e.g. /a/b/c/d.rst and directory is /a/b, the common prefix is /a/b
    common_prefix = os.path.commonprefix([full_path, directory])
    return common_prefix == directory

def format_size(size):
        prefixes = ["", "k", "M", "G", "T", "P", "E"]
        for p in prefixes:
            if(size < 1000):
                if p == "":
                    return f"{size}B"
                else:
                    return f"{size:.1f}{p}B"
            size /= 1000
        return f"{1000*size:1f}{prefixes[-1]}B"

async def serve_static_file_helper(req_path, base, download):
    # Joining the base and the requested path
    abs_path = os.path.join(base, req_path)
    
    verify_abs_path = abs_path
    if os.path.isdir(abs_path):
        verify_abs_path = os.path.join(abs_path, "")

    # Return 403
    if not in_directory(verify_abs_path, base):
        return abort(403)
    
    # Return 404 if path doesn't exist
    if not os.path.exists(abs_path):
        return abort(404)

    # Check if path is a file and serve
    if os.path.isfile(abs_path):
        #Add folder into download for file name in download mode
        return await send_file(abs_path, as_attachment=download, attachment_filename="_".join(req_path.split("/")[-2:]))
    
    return None

async def serve_static_file_only(req_path, base, download):
    res = await serve_static_file_helper(req_path, base, download)

    if res is not None:
        return res
    
    return abort(404)

async def serve_static_folder(req_path, base, download):
    abs_path = os.path.join(base, req_path)

    res = await serve_static_file_helper(req_path, base, download)

    if res is not None:
        return res
    
    web_base = os.path.join(request.path, "")

    # Show directory contents
    files = sorted(os.listdir(abs_path))
    files = [{
        "name": fn,
        "size": format_size(os.path.getsize(os.path.join(abs_path, fn))),
        "isdir": os.path.isdir(os.path.join(abs_path, fn))
        } for fn in files]
    return await render_template("files.html", files=files, base_dir=web_base, parent_dir = os.path.dirname(web_base.rstrip("/")))
