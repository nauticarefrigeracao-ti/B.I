import sys
sys.path.insert(0, r'C:\Users\Pichau\analise_progress')
import importlib.util, importlib
spec = importlib.util.find_spec('app_streamlit')
print('spec found:', bool(spec))
mod = importlib.import_module('app_streamlit')
print('import ok, main exists:', hasattr(mod, 'main'))
