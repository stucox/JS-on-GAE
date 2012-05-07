# Quick mock for ctypes.c_int to make pyjon.interpr work in pure Python
# environments

class c_int(object):
    def __init__(self, val):
        self.value = int(val)

