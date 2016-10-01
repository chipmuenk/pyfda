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
fil_inst = ""

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


    def create_fil_inst(self, fd):
        """
        Create an instance of the filter design method passed as string "fd" 
        from the module found in ``fd_module_names[fd]``.
        This dictionary has been collected by filter_tree_builder.py. 
        
        The instance can then be referenced as the global ``fil_inst``.

    
        Parameters
        ----------
        
        fd : string
            The name of the filter design class to be instantiated (e.g. 'cheby1' or 'equiripple')
    
        Returns
        -------
        
        err_code : integer
            :-1: filter design class was instantiated successfully
            
            :0: filter instance exists, no re-instantiation necessary
             
            :1: filter class name not found in dict 'fd_module_names'
             
            :2: filter class could not be imported 
             
            :3: unknown error during instantiation
        
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
            # Try to dynamically import the module fd from package 'filter_design'
            # i.e. do the following
            # import pyfda.filter_design.<fd> as fd_module  
            #------------------------------------------------------------------
            fd_module = importlib.import_module(fb.fd_module_names[fd])
            #------------------------------------------------------------------

        except KeyError as e:
            err_string =("\nKeyError in 'FilterFactory.create_fil_inst()':\n"
                  "Filter design module '%s' not in dict 'fd_module_names',\n"
                  "i.e. it was not found by 'FilterTreeBuilder'."%fd)
            self.err_code = 1
            print(err_string)
            return self.err_code
            
        except ImportError as e:
            # Filter module fd is in dictionary 'fd_module_names', 
            # but could not be imported.
            err_string =("\nImportError in 'FilterFactory.create_fil_inst()':\n"
                  "Filter design module '%s' could not be imported."%fd)
            self.err_code = 2
            print(err_string)
            return self.err_code

        # Check whether create_fil_inst has been called for the first time . 
        # (= no filter object and hence no attribute 'name' exists) or whether 
        # the design method has been changed since last time. 
        # In both cases, a (new) filter object is instantiated.

        if (not hasattr(fil_inst, 'name') or fd != fil_inst.name):
            # get named attribute from dm_module, here, this returns a class
            fil_class = getattr(fd_module, fd, None)
            fil_inst = fil_class() # instantiate an object         
            self.err_code = -1 # filter instance has been created / changed successfully

        elif not fil_class: # dm is not a class of dm_module
            err_string = ("\nERROR in 'FilterFactory.create_fil_inst()':\n"
                    "Unknown design class '%s', could not be created.", fd)
            print(err_string)
            self.err_code = 3
        else:
            err_string = ""
            self.err_code = 0
            logger.debug("FilterFactory.create_fil_inst(): successfully created %s", fd)
        
        return self.err_code

#------------------------------------------------------------------------------      
    def call_fil_method(self, method, fil_dict, fd = None):
        """
        Instantiate the filter design class passed  as string `fd` with the 
        globally accessible handle `fil_inst`. If `fd = None`, use the previously
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

        fd : string (optional, default: None)
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
            
        >>> call_fil_method("LPmin", fd = "cheby1")(fil[0])
        
        The example first creates an instance of the filter class 'cheby1' and 
        then performs the actual filter design by calling the method 'LPmin',
        passing the global filter dictionary fil[0] as the parameter.
    
        """                
        if fd: # filter design class was part of the argument, (re-)create class instance
            self.create_fil_inst(fd)

        # Error during filter design class instantiation (class fd could not be instantiated)           
        if self.err_code > 0 and self.err_code < 16:
            err_string = "Filter design class could not be instantiated, see previous error message."
            return self.err_code
            
        # test whether 'method' is a string or unicode type under Py2 and Py3:
        elif not isinstance(method, six.string_types):
            err_string = "Method name '{0}' is not a string.".format(method)
            self.err_code = 16
            
        # method does not exist in filter class:           
        elif not hasattr(fil_inst, method):
            err_string = "Method '{0}' doesn't exist in class '{1}'.".format(method, fil_inst)
            self.err_code = 17
 
        else:
            try:
                #------------------------------------------------------------------
                getattr(fil_inst, method)(fil_dict)
                #------------------------------------------------------------------
            except Exception as e:
                err_string =("\Error calling %s':\n"%method, e)
                self.err_code = 18
            else: # no error, keep old error code
                err_string = ""
                
        if self.err_code > 0:
                logger.error(err_string)
                print("\nERROR in 'FilterFactory.select_fil_method()':")
                print(err_string)
            
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
    print("\nfd_module_names\n", fb.fd_module_names)
    print("aaa:", fil_factory.create_fil_inst("aaa"),"\n") # class doesn't exist
    print("cheby1:", fil_factory.create_fil_inst("cheby1"),"\n") # first time inst.
    print("cheby1:", fil_factory.create_fil_inst("cheby1"),"\n") # second time inst.
    print("cheby2:", fil_factory.create_fil_inst("cheby2"),"\n") # new class
    print("bbb:", fil_factory.create_fil_inst("bbb"),"\n") # class doesn't exist
    
    print("LPman, fd = cheby2:", fil_factory.call_fil_method("LPman", fb.fil[0], fd = "cheby2"),"\n")
    print("LPmax:", fil_factory.call_fil_method("LPmax", fb.fil[0]),"\n") # doesn't exist
    print("Int 1:", fil_factory.call_fil_method(1, fb.fil[0]),"\n") # not a string
    print("LPmin:", fil_factory.call_fil_method("LPmin", fb.fil[0]),"\n") # changed method
    
    print("LPmin:", fil_factory.call_fil_method("LPmin", fb.fil[0]),"\n")
    print("LP:", fil_factory.call_fil_method("LP", fb.fil[0]),"\n")
    print("LPman, fd = cheby1:", fil_factory.call_fil_method("LPman", fb.fil[0], fd = "cheby1"),"\n")
    
    print("LPman, fd = cheby1:", fil_factory.call_fil_method("LPman", fd = "cheby1"),"\n")
   