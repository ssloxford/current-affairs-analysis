cd "$(dirname "$0")"

# Install packages
sudo apt update
sudo apt install python3-pip "fonts-cmu" python3-venv

# Download data
wget "https://zenodo.org/records/14712107/files/data.zip?download=1" -O data.zip
unzip data.zip -d data

# Create venv
python3 -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

# Run notebook
#python3 -m jupyter execute plots.ipynb
# Run dataset
#python3 -m proc_code.webserver
