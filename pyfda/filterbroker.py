# -*- coding: utf-8 -*-
"""
filterbroker.py

Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing filterbroker.py runs the module once, defining all module variables.
Module variables are global like class variables. 


Author: Christian Muenker
"""

from __future__ import division, unicode_literals, print_function, absolute_import
import importlib
import logging
import six

logger = logging.getLogger(__name__)
# Project base directory
base_dir = ""

# Instance of current filter design class (e.g. "cheby1")
fil_inst = ""

# Current method of current filter design class (e.g. cheby1.LPmin)
fil_method = ""

# State of filter design: "ok", "changed", "error", "failed"
design_filt_state = "changed"

# return error codes for class instantiation and method 
err_code = 99 # instantiated, not yet initialized

# module myhdl found?
MYHDL = False

# see http://stackoverflow.com/questions/9058305/getting-attributes-of-a-class
# see http://stackoverflow.com/questions/2447353/getattr-on-a-module


#==============================================================================
# The entries in this file are only used as initial / default entries and
# demonstrate the structure of the global dicts and lists.

#The actual entries are created resp. overwritten by
#
# ----- FilterTreeBuilder.__init__() ------
# ------                 .buildFilTree()
#
# Dictionary with filter name and full module name
design_methods = {"equiripple":"pyfda.filter_design.equiripple",
                  "cheby1":"pyfda.filter_design.cheby1",
                  "cheby2":"pyfda.filter_design.cheby2"}

# Dictionary with translations between short class names and long names for
# design methods
dm_names = {#IIR
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
            'W_PB':1., 'W_PB2':1., 'W_SB':1., 'W_SB2':1.,
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
class FilterFactory(object):
    """
    This class implements a filter facory that (re)creates the globally accessible
    filter instance "fil_inst" from module path and class name, passed as strings.
    """
    def __init__(self):
        #--------------------------------------
        pass



    def create_fil_inst(self, dm):
        """
        Create an instance of "dm" from the module found in design_methods[dm].
        This dictionary has been collected by filter_tree_builder.py. 
        
        The instance can then be referenced as the global 'fil_inst'.

    
        Parameters
        ----------
        dm: string
    
            The name of the design method to be constructed (e.g. 'cheby1' or 'equiripple')
    
        Returns
        -------
        err_code: integer
            -2: new filter instance was created sucessfully
            -1: filter instance was created for the first time
             0: filter instance exists, no re-instantiation necessary
             1: filter class (module) could not be imported
             2: filter class was imported, but could not be instantiated.

             17: filter method in argument is not a string
             18: filter method does not exist in class 
             19: filter method is not callable
             
        
        Example
        -------
            
        >>> create_instance('cheby1')
        >>> fil_inst.LPmin(fil[0])
        
        The example first creates an instance of the filter class 'cheby1' and 
        then performs the actual filter design by calling the method 'LPmin',
        passing the global filter dictionary fil[0] as the parameter.
    
        """
   
        global fil_inst  # this allows _WRITING_ to fil_inst
        global err_code
        
        try:
            # Try to dynamically import the module dm from package 'filter_design'
            dm_module = importlib.import_module(design_methods[dm])

        except (ImportError, KeyError) as e:
            # Filter class dm is not in dictionary 'design_methods', 
            # i.e. it was not found by FilterTreeBuilder.
            print("Exception:", e)
            self.err_string =("\nERROR in 'FilterFactory.create_fil_inst()':\n"
                  "Filter design class '%s' could not be imported."%dm)
            err_code = 1
            print(self.err_string)
            return err_code
            
        # Check whether create_fil_inst is called for the first time
        #    (= no filter object exists, AttributeError is raised). 
        # If not, check whether the design method has been changed. 
        # In both cases, a (new) filter object is instantiated.

        try: # has a filter object been instantiated yet?           
            if dm != fil_inst.name: # Yes (if no error occurs), check name
                inst = getattr(dm_module, dm, None)
                fil_inst = inst()
                err_code = -2 # design class has been changed
                return err_code

        except AttributeError as e: # No, create a filter instance
            inst = getattr(dm_module, dm, None)
            fil_inst = inst()
            err_code = -1 # filter instance has been created for the first time

        if not inst: # dm is not a class of dm_module
            self.err_string = ("\nERROR in 'FilterFactory.create_fil_inst()':\n"
                    "Unknown design class '%s', could not be created.", dm)
            print(self.err_string)
            err_code = 2
        else:
            self.err_string = ""
            err_code = 0
            logger.debug("FilterFactory.create_fil_inst(): created %s", dm)
        
        return err_code

#------------------------------------------------------------------------------      
    def create_fil_method(self, method, dm = None):
        """
        Create a global reference `fil_method` to the method passed as string `method`
        of the filter class instantiated before as `fil_inst` (global).         . 

    
        Parameters
        ----------
        method: string
    
            The name of the design method to be constructed (e.g. 'LPmin')

        dm: string (optional, default: None)
    
            The name of the design class to be instantiated
    
        Returns
        -------
        err_code: integer
             0: filter method exists and is callable
             17: passed argument is not a string
             18: filter does not exist in class 
             19: filter class was imported, but could not be instantiated..
        
        Example
        -------
            
        >>> create_instance('cheby1')
        >>> fil_inst.LPmin(fil[0])
        
        The example first creates an instance of the filter class 'cheby1' and 
        then performs the actual filter design by calling the method 'LPmin',
        passing the global filter dictionary fil[0] as the parameter.
    
        """
        global fil_method # this allows _WRITING_ to fil_method
        global err_code
        
        fil_method = None
        
        if dm:
            self.create_fil_inst(dm)
        if err_code > 0 and err_code < 17: # class dm could not be instantiated
            return err_code
        # test whether 'method' is a string or unicode type under Py2 and Py3
        if not isinstance(method, six.string_types):
            self.err_string = "Method '{0}' is not a string.".format(method)
            err_code = 17
        else:
            #------------------------------------------------------------------
            fil_method = getattr(fil_inst, method, None) # returns None if attribute doesn't exist
            #------------------------------------------------------------------
            if not fil_method:
                self.err_string = "Method '{0}' doesn't exist in class '{1}'.".format(method, fil_inst)
                err_code = 18
    
            elif not callable(fil_method):
                self.err_string = "Method '{0}' of class '{1}' is not callable.".format(method, fil_inst)
                err_code = 19
            else:
                err_code = 0 # no error
                self.err_string = ""
                
        if err_code > 0:
                print("\nERROR in 'FilterFactory.select_fil_method()':")
                print(self.err_string)
            
        return err_code
        
# TODO:      Generate Signal in filter_design: finished, error, ...
        
#------------------------------------------------------------------------------            
    def call_fil_method(self, *method, **dm): 
    # pass positional and keyword arguments to create_fil_method
        """
        Dynamically select and call the method passed as string "method" 
        of the filter class instantiated as the global `fil_inst`. A reference
        to the selected filter design method is stored as `fil_method` and can
        be called subsequently using `fil_method(my_params)`.
        
        E.g.  call_method('LP'+'min')
    
        Parameters
        ----------
        method: string
    
            The name of the design method to be called (e.g. 'LPmin')
            
        dm: string (optional, default: None)
    
            The name of the design class to be instantiated
            
        Returns
        -------
        Error code
    
        """
   
        global fil_method   # this allows _WRITING_ to fil_method
        # dynamically select the method given by  fil_inst.method:
        err_code = self.create_fil_method(*method, **dm) 
        if err_code < 1:
            fil_method(fil[0])
        return err_code
        
#------------------------------------------------------------------------------
        
# This instance of FilterFactory is globally visible!
fil_factory = FilterFactory()

###############################################################################
"""
See also on data persistence and global variables:
http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
http://pymotw.com/2/articles/data_persistence.html

Alternative approaches for data persistence: Module shelve or pickleshare

"""
if __name__ == '__main__':
    print("design_methods\n", design_methods)
    print(fil_factory.create_fil_inst("aaa"), err_code) # class doesn't exist
    print(fil_factory.create_fil_inst("cheby1"), err_code) # first time inst.
    print(fil_factory.create_fil_inst("cheby1"), err_code) # second time inst.
    print(fil_factory.create_fil_inst("cheby2"), err_code) # new class
    print(fil_factory.create_fil_inst("bbb"), err_code) # class doesn't exist
    
    
    print(fil_factory.create_fil_method("LPman", dm = "cheby2"), err_code)
    print(fil_factory.create_fil_method("LPmax"), err_code) # doesn't exist
    print(fil_factory.create_fil_method(1), err_code) # not a string
    print(fil_factory.create_fil_method("LPmin"), err_code) # changed method
    
    print(fil_factory.call_fil_method("LPmin"), err_code)
    print(fil_factory.call_fil_method("LP"), err_code)
    print(fil_factory.call_fil_method("LPman", dm = "cheby1"), err_code)
    # 
    
