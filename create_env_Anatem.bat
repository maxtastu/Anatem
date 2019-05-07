@echo off

set http_proxy=<url proxy http>
set https_proxy=<url proxy https>

conda env create --file <D:\libbdimage_light-1.0.0\conda.yml> --name env_Anatem
call activate env_Anatem
pip install pendulum
cd <D:\libhydro\libhydro-0.5.3>
python setup.py install
conda install matplotlib pyqt=4 numpy pandas lxml pyodbc scipy

call deactivate