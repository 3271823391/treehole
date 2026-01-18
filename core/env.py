import os

def init_env():
    os.environ["FLAGS_use_mkldnn"] = "0"
    os.environ["FLAGS_enable_pir_api"] = "0"
    os.environ["FLAGS_new_executor"] = "0"
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"