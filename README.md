Data and analysis scripts for "Current Affairs: A Security Measurement Study of CCS EV Charging Deployments"

## Project organization

#### Device IDs

Tested chargers are divided into four layers:
- Countries
- Charging Parks: (A set of multiple chargers deployed in the same location by the same operator)
- Chargers: Boxes inside of a park.
- Plugs: The individual plugs. (Usually 1 or 2 per charger)

Each device is given a unique ID for dataset management in the format: `<country code>.<park ID>.<charger ID>.<plug ID>`. The code heavily assumes that the below file/folder naming conventions are used, and that none of the ID components contain a `.` or `_`.

#### Data format

Data is stored in the `data/` folder, the contents of this are provided as a separate Zip file [on Zenodo](https://zenodo.org/records/14712107), and must be extract to this location without additional nested `data` directories.

**High level information** about the parks, charger and plugs (location, manufacturer, serial number) is stored in three metadata CSV files in `data/metadata/`.

**Experimental data** for each plug is stored in `data/chargers/<country code>/<park ID>/<charger ID>_<plug ID>/`.

**Each experiment** has a folder indexed by a UTC timestamp `YYYY_MM_DD_hh_mm_ss` inside the plug folder. For each experiment there is a `result.json` file from the measurement tool, as well as a `backup.bak.txt` that is flushed to disk line by line in case the data collector crashes. The analysis scripts can automatically re-generate a damaged result file from the backup. Both of these files contain a full record of every action and command the test tool executed against the charger. For each charger a `pcap.pcap` file is also recorded of the test.

During processing, the user is prompted to inspect NMKs for visible patterns. The results of this are cached in `nmk_review.json` for each plug.

**Processed data** of each experiment is saved to an `overview.json` file for each plug, listing the final conclusions. In some cases where an old version of the test tool was used, we only have these overview files.

**Photos** are stored in `data/photos`, named based on UTC timestamp, and split into folders by day. The metadata files specify which photos belong to which devices.

According to our dataset anonymity discussed in the paper, metadata, photos, and `overview.json` files are provided, but the raw experiments are not.

#### Code files

The code was written in Python 3.9 on Windows 10.
It has also been tested in Python 3.12 on Kubuntu 24.04.1 LTS, the remaining instructions are for this version.
Only standard packages are used, the code should be portable to most platforms and future versions.

To set up, download the repository, and execute
```sh
./install.sh
source venv/bin/activate
```

This installs the necessary system packages, downloads our dataset, creates a Python venv in the folder `venv`, and installs the necessary packages.

The `proc_code/` folder contains a small python library for loading, managing and analysing data in accordance with the above format.

Inside this, the `proc_code/webserver/` folder contains a small webserver that allows interactive management of the data.
To launch the server, in the folder of this `md` file run `python3 -m proc_code.webserver`
Open http://localhost:8000 for a static view or http://localhost:8000?edit to manage the data.

**Warning:** Do not edit any data file or use any other script while the webserver is running. On exit (SIGINT) it will save the data back to disk, overwriting any external changes.

To build a safe to view static website from the data, run `python3 -m proc_code.build_static`. This will start the webserver, `wget` each page, export a static HTML website into the `data/` folder. This can then be hosted using any static webserver, such as `python3 -m http.server`. For simplicity, `.sh` and `.bat` files are provided in `data/` to help with this.

## Adding data

To add new experiments, the following steps are necessary:
- Create metadata entries for each new park, charger and plug. This can be done by editing the CSV or using the webserver. Do not do both at the same time.
- Add the experimental folders from the data collector to the correct folders for each plug
- Run `python3 -m proc_code.process_data` in the root folder. This will interactively prompt about the NMKs for the new devices, for a human to review whether they appear to have a pattern.

## Running analysis

The `plots.ipynb` file can be used to generate statistics and plots from the data. This can be ran using only the dataset we publish.
To run this in a non-interactive way, run `python3 -m jupyter execute plots.ipynb`.