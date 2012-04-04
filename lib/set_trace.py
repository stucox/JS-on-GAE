# Rewire pdb so it works with AppEngine
def set_trace():
    """Rewires pdb to work with appengine. """

    import pdb
    import sys
    pdb.Pdb(
        stdin=getattr(sys,'__stdin__'),
        stdout=getattr(sys,'__stderr__')).set_trace(sys._getframe().f_back)
