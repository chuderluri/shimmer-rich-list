git submodule update --init --recursive
python -m venv venv
call .\venv\Scripts\activate
cd iota.rs\client\bindings\python\native
pip install -r requirements-dev.txt
pip install -e .
cd ..\..\..\..\..
pip install -r requirements.txt