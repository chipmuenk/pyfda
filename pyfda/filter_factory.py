# -*- coding: utf-8 -*-
"""
filter_factory.py

Dynamic parameters and settings are exchanged via the dictionaries in this file.
Importing filterbroker.py runs the module once, defining all module variables.
Module variables are global like class variables. 


Author: Christian Muenker
"""

from __future__ import division, unicode_literals, print_function, absolute_import
import importlib
import logging
import six
from . import filterbroker as fb

logger = logging.getLogger(__name__)

# Instance of current filter design class (e.g. "cheby1")
fil_inst = None

#------------------------------------------------------------------------------
class FilterFactory(object):
    """
    This class implements a filter factory that (re)creates the globally accessible
    filter instance "fil_inst" from module path and class name, passed as strings.
    """
    def __init__(self):
        #--------------------------------------
        # return error codes for class instantiation and method 
        self.err_code = 0


    def create_fil_inst(self, fc, mod = None):
        # TODO: need to pass both module and class name for more flexibility
        """
        Create an instance of the filter design class passed as string "fc" 
        from the module found in ``fb.fil_classes[fc]``.
        This dictionary has been collected by filter_tree_builder.py. 
        
        The instance can afterwards be referenced as the global ``fil_inst``.

    
        Parameters
        ----------
        
        fc : string
            The name of the filter design class to be instantiated (e.g. 'cheby1' or 'equiripple')

        mod : string (optional, default = None)
            Fully qualified name of the filter module. When not specified, it is
            read from the global dict ``fb.fil_classes``
            
        Returns
        -------
        
        err_code : integer
            :-1: filter design class was instantiated successfully
            
            :0: filter instance exists, no re-instantiation necessary
             
            :1: filter module not found by FilterTreeBuilder
             
            :2: filter module found by FilterTreeBuilder but could not be imported 
             
            :3: filter class could not be instantiated

            :4: unknown error during instantiation
        
        Example
        -------
            
        >>> create_fil_instance('cheby1')
        >>> fil_inst.LPmin(fil[0])
        
        The example first creates an instance of the filter class 'cheby1' and 
        then performs the actual filter design by calling the method 'LPmin',
        passing the global filter dictionary fil[0] as the parameter.
    
        """
        global fil_inst # allow writing to variable

        try:
            # Try to dynamically import the module fc, i.e. do the following
            # import pyfda.<filter_package>.<fc> as fc_module  
            if not mod:            
                mod = fb.fil_classes[fc]['mod']
            #------------------------------------------------------------------
            fc_module = importlib.import_module(mod)                
            #------------------------------------------------------------------                

        except KeyError as e:
            err_string =("\nKeyError in 'FilterFactory.create_fil_inst()':\n"
                  "Filter design class '%s' is not in dict 'fb.fil_classes',\n"
                  "i.e. it was not found by 'FilterTreeBuilder'."%fc)
            self.err_code = 1
            logger.warning(err_string)
            return self.err_code
            
        except ImportError as e:
            # Filter module mod is in dictionary 'fb.fil_classes', but could not be imported.
            err_string =("\nImportError in 'FilterFactory.create_fil_inst()':\n"
                  "Filter design module '%s' could not be imported."%str(mod))
            self.err_code = 2
            logger.warning(err_string)
            return self.err_code

        # Check whether create_fil_inst has been called for the first time . 
        # (= no filter object and hence no attribute 'name' exists) or whether 
        # the design method has been changed since last time. 
        # In both cases, a (new) filter object is instantiated.

        if fil_inst is None or fc != fil_inst.__class__.__name__: 
            err_string = ""
            self.err_code = -1
            # get attribute fc from fc_module, here, this returns the class fc
            fil_class = getattr(fc_module, fc, None) # or None if not in fc_module 

            if fil_class is None: # fc is not a class of fc_module
                err_string = ("\nERROR in 'FilterFactory.create_fil_inst()':\n"
                        "Unknown design class '%s', could not be created." %fc)
                logger.warning(err_string)
                self.err_code = 3
            else:
                try:
                    fil_inst = fil_class() # instantiate an object         
                    self.err_code = 0 # filter instance has been created / changed successfully
                    logger.debug("FilterFactory.create_fil_inst(): successfully created %s", fc)
                except Exception as e:
                    self.err_code = 4
                    logger.warning("Error during instantiation of filter class {0}:\n{1}".format(fc,e))                    
        return self.err_code

#------------------------------------------------------------------------------      
    def call_fil_method(self, method, fil_dict, fc = None):
        """
        Instantiate the filter design class passed  as string `fc` with the 
        globally accessible handle `fil_inst`. If `fc = None`, use the previously
        instantiated filter design class. 
        
        Next, call the method passed as string `method` of the instantiated
        filter design class.
    
        Parameters
        ----------
        
        method : string
            The name of the design method to be called (e.g. 'LPmin')
            
        fil_dict : dictionary
            A dictionary with all the filter specs that is passed to the actual
            filter design routine. This is usually a copy of fb.fil[0]
            The results of the filter design routine are written back to the same dict.

        fc : string (optional, default: None)
            The name of the filter design class to be instantiated. When nothing
            is specified, the last filter selection is used.
    
        Returns
        -------
        
        err_code : integer
             :00: filter design method exists and is callable
             
             :16: passed method name is not a string
             
             :17: filter design method does not exist in class
             
             :18: filter design method is not callable
             
        
        Example
        -------
            
        >>> call_fil_method("LPmin", fc = "cheby1")(fil[0])
        
        The example first creates an instance of the filter class 'cheby1' and 
        then performs the actual filter design by calling the method 'LPmin',
        passing the global filter dictionary fil[0] as the parameter.
    
        """                
        if self.err_code >= 16:
            self.err_code = 0 #  # clear previous method call error
            err_string = ""

        if fc: # filter design class was part of the argument, (re-)create class instance
            self.err_code = self.create_fil_inst(fc)

        # Error during filter design class instantiation (class fc could not be instantiated)           
        if self.err_code > 0:
            err_string = "Filter design class could not be instantiated, see previous error message."
            
        # Test whether 'method' is a string or unicode type under Py2 and Py3:
        elif not isinstance(method, six.string_types):
            err_string = "Method name '{0}' is not a string.".format(method)
            self.err_code = 16
            
        # method does not exist in filter class:           
        elif not hasattr(fil_inst, method):
            err_string = "Method '{0}' doesn't exist in class '{1}'.".format(method, fil_inst)
            self.err_code = 17
 
        else: # everything ok so far, try calling method with the filter dict as argument
            try:
                #------------------------------------------------------------------
                getattr(fil_inst, method)(fil_dict)
                #------------------------------------------------------------------
            except Exception as e:
                err_string = "\nError calling method '{0}' of class '{1}':\n{2}"\
                                    .format(method, type(fil_inst).__name__, e)
                self.err_code = 18
                
        if self.err_code > 0:
                logger.error("Err. Code {0}:\n{1}".format(self.err_code, err_string))
            
        return self.err_code
        
# TODO:      Generate Signal in filter_design: finished, error, ...
                    
#------------------------------------------------------------------------------
fil_factory = FilterFactory()       
# This *class instance* of FilterFactory can be accessed in other modules using
# import filter_factory as ff
# ff.fil_factory. ...


###############################################################################
"""
See also on data persistence and global variables:
http://stackoverflow.com/questions/13034496/using-global-variables-between-files-in-python
http://stackoverflow.com/questions/1977362/how-to-create-module-wide-variables-in-python
http://pymotw.com/2/articles/data_persistence.html

Alternative approaches for data persistence: Module shelve or pickleshare

"""
if __name__ == '__main__':
    print("\nfb.fil_classes\n", fb.fil_classes)
    print("aaa:", fil_factory.create_fil_inst("aaa"),"\n") # class doesn't exist
    print("cheby1:", fil_factory.create_fil_inst("cheby1"),"\n") # first time inst.
    print("cheby1:", fil_factory.create_fil_inst("cheby1"),"\n") # second time inst.
    print("cheby2:", fil_factory.create_fil_inst("cheby2"),"\n") # new class
    print("bbb:", fil_factory.create_fil_inst("bbb"),"\n") # class doesn't exist
    
    print("LPman, fc = cheby2:", fil_factory.call_fil_method("LPman", fb.fil[0], fc = "cheby2"),"\n")
    print("LPmax:", fil_factory.call_fil_method("LPmax", fb.fil[0]),"\n") # doesn't exist
    print("Int 1:", fil_factory.call_fil_method(1, fb.fil[0]),"\n") # not a string
    print("LPmin:", fil_factory.call_fil_method("LPmin", fb.fil[0]),"\n") # changed method
    
    print("LPmin:", fil_factory.call_fil_method("LPmin", fb.fil[0]),"\n")
    print("LP:", fil_factory.call_fil_method("LP", fb.fil[0]),"\n")
    print("LPman, fc = cheby1:", fil_factory.call_fil_method("LPman", fb.fil[0], fc = "cheby1"),"\n")
    
    print("LPman, fc = cheby1:", fil_factory.call_fil_method("LPman", fc = "cheby1"),"\n") # fails
   