# -*- coding: utf-8 -*-
"""
filterbroker.py

Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing filterbroker.py runs the module once, defining all module variables.
Module variables are global like class variables. 


Author: Christian Muenker
"""

from __future__ import division, unicode_literals, print_function, absolute_import
#import importlib
#import logging
#import six

#logger = logging.getLogger(__name__)
# Project base directory
base_dir = ""

# State of filter design: "ok", "changed", "error", "failed"
design_filt_state = "changed"

# module myhdl found?
MYHDL = False

# see http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class
# see http://stackoverflow.com/questions/2447353/getattr-on-a-module


#==============================================================================
# The entries in this file are only used as initial / default entries and
# demonstrate the structure of the global dicts and lists.
# They are also handy for module-level testing.

#The actual entries are created resp. overwritten by
#
# ----- FilterTreeBuilder.__init__() ------
# ------                 .buildFilTree()
#
# Dictionary with filter design class name and full module name
fd_module_names = {"equiripple":"pyfda.filter_design.equiripple",
                  "cheby1":"pyfda.filter_design.cheby1",
                  "cheby2":"pyfda.filter_design.cheby2"}

# Dictionary with translations between short and long names for filter design classes
fd_names = {# IIR:
            "butter":"Butterworth", "cheby1":"Chebychev 1",
            "bessel":"Bessel", "cheby2":"Chebychev 2",
            # FIR:
            "equiripple":"Equiripple", "firls":"Least-Square",
            "firwin":"Windowed"}

# Dictionary describing the available combinations of response types (rt),
# filter types (ft), design methods (dm) and filter order (fo).
vis_man = ['fo','fspecs','tspecs'] # manual filter order
vis_min = ['fo','fspecs','tspecs'] # minimum filter order
dis_man = [] # manual filter order
dis_min = ['fspecs'] # minimum filter order
msg_min = "minimum"
msg_man = "maximum"
fil_tree = {
    'HP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'A_PB', 'F_PB'],
                         "vis":vis_man, "dis":dis_man, "msg":msg_man},
                 'min': {"par":['A_SB', 'A_PB', 'F_SB', 'F_PB'],
                         "vis":vis_min, "dis":dis_min, "msg":msg_min}}},
         'IIR':
             {'cheby1':
                 {'man': {"par":['N', 'A_PB', 'F_PB'],
                          "vis":vis_man, "dis":dis_man, "msg":msg_man},
                  'min': {"par":['A_SB', 'A_PB', 'F_SB', 'F_PB'],
                          "vis":vis_min, "dis":dis_min, "msg":msg_min}},
              'cheby2':
                  {'man': {"par":['N', 'A_SB', 'F_SB'],
                           "vis":vis_man, "dis":dis_man, "msg":msg_man},
                   'min': {"par":['A_SB', 'A_PB', 'F_SB', 'F_PB'],
                           "vis":vis_min, "dis":dis_min, "msg":msg_min}}}},
    'BP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2', 'W_PB', 'W_SB', 'W_SB2'],
                         "vis":vis_man, "dis":dis_man, "msg":msg_man}}},
         'IIR':
             {'cheby1': {'man': {"par":['N', 'A_PB', 'F_PB', 'F_PB2'], 
                                 "vis":vis_man, "dis":dis_man, "msg":msg_man},
                         'min': {"par":['A_PB', 'A_SB', 'F_SB', 'F_PB', 'F_PB2', 'F_SB2'],
                                 "vis":vis_min, "dis":dis_min, "msg":msg_min}},
              'cheby2': {'man': {"par":['N', 'A_SB', 'F_SB', 'F_SB2'],
                                 "vis":vis_man, "dis":dis_man, "msg":msg_man},
                         'min': {"par":['A_PB', 'A_SB','F_SB',  'F_PB', 'F_PB2', 'F_SB2'],
                                 "vis":vis_min, "dis":dis_min, "msg":msg_min}}}},
    'LP':
        {'FIR':
            {'equiripple':
                {'man': {"par":['N', 'A_PB', 'F_PB'], 
                         "vis":vis_man, "dis":dis_man, "msg":msg_man},
                 'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB'],
                         "vis":vis_min, "dis":dis_min, "msg":msg_min}}},
         'IIR':
             {'cheby1':
                 {'man': {"par":['N', 'A_PB', 'F_PB'],
                          "vis":vis_man, "dis":dis_man, "msg":msg_man},
                  'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB'], 
                          "vis":vis_min, "dis":dis_min, "msg":msg_min}},
             'cheby2': {'man': {"par":['N', 'A_SB', 'F_SB'],
                                "vis":vis_man, "dis":dis_man, "msg":msg_man},
                        'min': {"par":['A_PB', 'A_SB', 'F_PB', 'F_SB'],
                                "vis":vis_min, "dis":dis_min, "msg":msg_min}
                        }
            }
        }
    }


# -----------------------------------------------------------------------------
# Dictionary containing current filter type, specifications, design and some
# auxiliary information, it is automatically overwritten by input widgets
# and design routines
#------------------------------------------------------------------------------

fil = [None] * 10 # create empty list with length 10 for multiple filter designs
# This functionality is not implemented yet, currently only fil[0] is used

fil[0] = {'rt':'LP', 'ft':'FIR', 'dm':'equiripple', 'fo':'man',
            'N':10, 'f_S':1,
            'A_PB':0.02, 'A_PB2': 0.01, 'F_PB':0.1, 'F_PB2':0.4, 'F_C': 0.2, 'F_N': 0.2,
            'A_SB':0.001, 'A_SB2': 0.0001, 'F_SB':0.2, 'F_SB2':0.3, 'F_C2': 0.4, 'F_N2': 0.4,
            'W_PB':1, 'W_PB2':1, 'W_SB':1, 'W_SB2':1,
            #
            'ba':([1, 1, 1], [3, 0, 2]), # tuple of bb, aa
            'zpk':([-0.5 + 3**0.5/2.j, -0.5 - 3**0.5/2.j],
                   [(2./3)**0.5 * 1j, -(2./3)**0.5 * 1j], 1),
            'q_coeff':{'QI':0, 'QF': 15, 'quant': 'round', 'ovfl': 'sat', 'frmt':'frac'},
            'sos': None,
            'creator':('ba','filterbroker'), #(format ['ba', 'zpk', 'sos'], routine)
            'amp_specs_unit':'dB',
            'freqSpecsRangeType':'Half',
            'freqSpecsRange': [0,0.5],
            'freq_specs_sort' : True,
            'freq_specs_unit' : 'f_S',
            'plt_fLabel':r'$f$ in Hz $\rightarrow$',
            'plt_fUnit':'Hz',
            'plt_tLabel':r'$n \; \rightarrow$',
            'plt_tUnit':'s',
            'plt_phiUnit': 'rad',
            'plt_phiLabel': r'$\angle H(\mathrm{e}^{\mathrm{j} \Omega})$  in rad ' + r'$\rightarrow $',
            'wdg_dyn':{'win':'hann'}
            }

#------------------------------------------------------------------------------
#==============================================================================
# class FilterFactory(object):
#     """
#     This class implements a filter factory that (re)creates the globally accessible
#     filter instance "fil_inst" from module path and class name, passed as strings.
#     """
#     def __init__(self):
#         #--------------------------------------
#         # return error codes for class instantiation and method 
#         self.err_code = 0
# 
# 
#     def create_fil_inst(self, fd):
#         """
#         Create an instance of the filter design method passed as string "fd" 
#         from the module found in ``fd_module_names[fd]``.
#         This dictionary has been collected by filter_tree_builder.py. 
#         
#         The instance can then be referenced as the global ``fil_inst``.
# 
#     
#         Parameters
#         ----------
#         
#         fd : string
#             The name of the filter design class to be instantiated (e.g. 'cheby1' or 'equiripple')
#     
#         Returns
#         -------
#         
#         err_code : integer
#             :-1: filter design class was instantiated successfully
#             
#             :0: filter instance exists, no re-instantiation necessary
#              
#             :1: filter class name not found in dict 'fd_module_names'
#              
#             :2: filter class could not be imported 
#              
#             :3: unknown error during instantiation
#         
#         Example
#         -------
#             
#         >>> create_fil_instance('cheby1')
#         >>> fil_inst.LPmin(fil[0])
#         
#         The example first creates an instance of the filter class 'cheby1' and 
#         then performs the actual filter design by calling the method 'LPmin',
#         passing the global filter dictionary fil[0] as the parameter.
#     
#         """
#    
#         global fil_inst  # this allows _WRITING_ to fil_inst
#                
#         try:
#             # Try to dynamically import the module fd from package 'filter_design'
#             # i.e. do the following
#             # import pyfda.filter_design.<fd> as fd_module  
#             #------------------------------------------------------------------
#             fd_module = importlib.import_module(fd_module_names[fd])
#             #------------------------------------------------------------------
# 
#         except KeyError as e:
#             err_string =("\nKeyError in 'FilterFactory.create_fil_inst()':\n"
#                   "Filter design module '%s' not in dict 'fd_module_names',\n"
#                   "i.e. it was not found by 'FilterTreeBuilder'."%fd)
#             self.err_code = 1
#             print(err_string)
#             return self.err_code
#             
#         except ImportError as e:
#             # Filter module fd is in dictionary 'fd_module_names', 
#             # but could not be imported.
#             err_string =("\nImportError in 'FilterFactory.create_fil_inst()':\n"
#                   "Filter design module '%s' could not be imported."%fd)
#             self.err_code = 2
#             print(err_string)
#             return self.err_code
# 
#         # Check whether create_fil_inst has been called for the first time . 
#         # (= no filter object and hence no attribute 'name' exists) or whether 
#         # the design method has been changed since last time. 
#         # In both cases, a (new) filter object is instantiated.
# 
#         if (not hasattr(fil_inst, 'name') or fd != fil_inst.name):
#             # get named attribute from dm_module, here, this returns a class
#             fil_class = getattr(fd_module, fd, None)
#             fil_inst = fil_class() # instantiate an object         
#             self.err_code = -1 # filter instance has been created / changed successfully
# 
#         elif not fil_class: # dm is not a class of dm_module
#             err_string = ("\nERROR in 'FilterFactory.create_fil_inst()':\n"
#                     "Unknown design class '%s', could not be created.", fd)
#             print(err_string)
#             self.err_code = 3
#         else:
#             err_string = ""
#             self.err_code = 0
#             logger.debug("FilterFactory.create_fil_inst(): successfully created %s", fd)
#         
#         return self.err_code
# 
# #------------------------------------------------------------------------------      
#     def call_fil_method(self, method, fil_dict, fd = None):
#         """
#         Instantiate the filter design class passed  as string `fd` with the 
#         globally accessible handle `fil_inst`. If `fd = None`, use the previously
#         instantiated filter design class. 
#         
#         Next, call the method passed as string `method` of the instantiated
#         filter design class.
#     
#         Parameters
#         ----------
#         
#         method : string
#             The name of the design method to be called (e.g. 'LPmin')
#             
#         fil_dict : dictionary
#             A dictionary with all the filter specs that is passed to the actual
#             filter design routine. This is usually a copy of fil[0]
#             The results of the filter design routine are written back to the same dict.
# 
#         fd : string (optional, default: None)
#             The name of the filter design class to be instantiated
#     
#         Returns
#         -------
#         
#         err_code : integer
#              :00: filter design method exists and is callable
#              
#              :16: passed method name is not a string
#              
#              :17: filter design method does not exist in class
#              
#              :18: filter design method is not callable
#              
#         
#         Example
#         -------
#             
#         >>> call_fil_method("LPmin", fd = "cheby1")(fil[0])
#         
#         The example first creates an instance of the filter class 'cheby1' and 
#         then performs the actual filter design by calling the method 'LPmin',
#         passing the global filter dictionary fil[0] as the parameter.
#     
#         """                
#         if fd: # filter design class was part of the argument, (re-)create class instance
#             self.create_fil_inst(fd)
# 
#         # Error during filter design class instantiation (class fd could not be instantiated)           
#         if self.err_code > 0 and self.err_code < 16:
#             err_string = "Filter design class could not be instantiated, see previous error message."
#             return self.err_code
#             
#         # test whether 'method' is a string or unicode type under Py2 and Py3:
#         elif not isinstance(method, six.string_types):
#             err_string = "Method name '{0}' is not a string.".format(method)
#             self.err_code = 16
#             
#         # method does not exist in filter class:           
#         elif not hasattr(fil_inst, method):
#             err_string = "Method '{0}' doesn't exist in class '{1}'.".format(method, fil_inst)
#             self.err_code = 17
#  
#         else:
#             try:
#                 #------------------------------------------------------------------
#                 getattr(fil_inst, method)(fil_dict)
#                 #------------------------------------------------------------------
#             except Exception as e:
#                 err_string =("\Error calling %s':\n"%method, e)
#                 self.err_code = 18
#             else: # no error, keep old error code
#                 err_string = ""
#                 
#         if self.err_code > 0:
#                 logger.error(err_string)
#                 print("\nERROR in 'FilterFactory.select_fil_method()':")
#                 print(err_string)
#             
#         return self.err_code
#         
# # TODO:      Generate Signal in filter_design: finished, error, ...
#                     
# #------------------------------------------------------------------------------
#         
# # This *class instance* of FilterFactory can be accessed in other modules using
# # import filterbroker as fb
# # fb.fil_factory. ...
# fil_factory = FilterFactory()
# 
# ###############################################################################
# """
# See also on data persistence and global variables:
# http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
# http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
# http://pymotw.com/2/articles/data_persistence.html
# 
# Alternative approaches for data persistence: Module shelve or pickleshare
# 
# """
# if __name__ == '__main__':
#     print("\nfd_module_names\n", fd_module_names)
#     print("aaa:", fil_factory.create_fil_inst("aaa"),"\n") # class doesn't exist
#     print("cheby1:", fil_factory.create_fil_inst("cheby1"),"\n") # first time inst.
#     print("cheby1:", fil_factory.create_fil_inst("cheby1"),"\n") # second time inst.
#     print("cheby2:", fil_factory.create_fil_inst("cheby2"),"\n") # new class
#     print("bbb:", fil_factory.create_fil_inst("bbb"),"\n") # class doesn't exist
#     
#     print("LPman, fd = cheby2:", fil_factory.call_fil_method("LPman", fd = "cheby2"),"\n")
#     print("LPmax:", fil_factory.call_fil_method("LPmax"),"\n") # doesn't exist
#     print("Int 1:", fil_factory.call_fil_method(1),"\n") # not a string
#     print("LPmin:", fil_factory.call_fil_method("LPmin"),"\n") # changed method
#     
#     print("LPmin:", fil_factory.call_fil_method("LPmin"),"\n")
#     print("LP:", fil_factory.call_fil_method("LP"),"\n")
#     print("LPman, fd = cheby1:", fil_factory.call_fil_method("LPman", fd = "cheby1"),"\n")
#==============================================================================
