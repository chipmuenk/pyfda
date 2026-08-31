# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
An instance of a filter design class (e.g. "Cheby1") is created with:

>>> from filter_factory import create_fil_instance, get_fil_inst
>>> create_fil_instance('Cheby1') # create instance of dynamic class
>>> get_fil_inst().LPmin(fil[0]) # design a filter
"""

import importlib
import logging
from pyfda.config_file_parser import ConfigFileParser as CFP
from pyfda.libs.pyfda_lib import debug_exception

logger = logging.getLogger(__name__)

# Class variable for instance of filter class
fil_inst = None

class FilterFactory():
    """
    This class implements a filter factory that (re)creates the class attribute
    ``fil_inst`` from module path and class name, passed as strings.
    """
    fil_inst = None

    def __init__(self):
        #--------------------------------------
        # return error codes for class instantiation and method
        self.err_code = 0

#------------------------------------------------------------------------------
    def create_fil_inst(self, fc: str, mod: str = "") -> int:
        """
        Create an instance of the filter design class passed as a string ``fc``
        from the module found in ``CFP.FILTER_CLASSES_DICT[fc]``.
        This dictionary has been collected by ``tree_builder.py``.

        The instance can afterwards be referenced as class attribute ``fil_inst`` of FilterFactory

        Parameters
        ----------

        fc : str
            The name of the filter design class to be instantiated (e.g. 'cheby1' or 'equiripple')

        mod : str (optional, default = "")
            Fully qualified name of the filter module. When not specified, it is
            read from the global dict ``CFP.FILTER_CLASSES_DICT[fc]['mod']``

        Returns
        -------

        err_code : int
          one of the following error codes:
            :-1: filter design class was instantiated successfully

            :0: filter instance exists, no re-instantiation necessary

            :1: filter module not found by FilterTreeBuilder

            :2: filter module found by FilterTreeBuilder but could not be imported

            :3: filter class could not be instantiated

            :4: unknown error during instantiation

        Examples
        --------

        >>> create_fil_instance('Cheby1')
        >>> fil_inst.LPmin(fil[0])

        The example first creates an instance of the filter class 'Cheby1' and
        then performs the actual filter design by calling the method 'LPmin',
        passing the global filter dictionary fil[0] as the parameter.

        """
        try:
            # Try to dynamically import the module fc, i.e. do the following
            # import pyfda.<filter_package>.<fc> as fc_module
            if mod == "":
                mod = CFP.FILTER_CLASSES_DICT[fc]['mod']
            #------------------------------------------------------------------
            fc_module = importlib.import_module(mod)
            #------------------------------------------------------------------

        except KeyError:
            err_string =("\nKeyError in 'FilterFactory.create_fil_inst()':\n"
                  f"Filter design class '{fc}' is not in dict 'CFP.FILTER_CLASSES_DICT',\n"
                  "i.e. it was not found by 'FilterTreeBuilder'.")
            self.err_code = 1
            logger.warning(err_string)
            debug_exception()
            return self.err_code

        except ImportError:
            # Filter module 'mod' is in dictionary 'CFP.FILTER_CLASSES_DICT',
            # but could not be imported:
            err_string =("\nImportError in 'FilterFactory.create_fil_inst()':\n"
                  f"Filter design module '{mod}' could not be imported.")
            self.err_code = 2
            logger.warning(err_string)
            debug_exception()
            return self.err_code

        # Check whether create_fil_inst has been called for the first time .
        # (= no filter object and hence no attribute 'name' exists) or whether
        # the design method has been changed since last time.
        # In both cases, a (new) filter object is instantiated.

        if FilterFactory.fil_inst is None or fc != FilterFactory.fil_inst.__class__.__name__:
            err_string = ""
            self.err_code = -1
            # get attribute fc from fc_module, here, this returns the class fc
            fil_class = getattr(fc_module, fc, None) # or None if fc not in fc_module

            if fil_class is None: # fc is not a class of fc_module
                err_string = ("\nERROR in 'FilterFactory.create_fil_inst()':\n"
                              f"Unknown filter class '{fc}', could not be created.")
                logger.warning(err_string)
                self.err_code = 3
            else:
                try:
                    FilterFactory.fil_inst = fil_class() # instantiate an object
                    self.err_code = 0 # filter instance has been created / changed successfully
                    logger.debug(
                        "FilterFactory.create_fil_inst(): successfully created '%s'", fc)
                except Exception as e:
                    self.err_code = 4
                    logger.warning(
                        "Error during instantiation of filter class '%s':\n%s", fc, e)
                    debug_exception()
                    #x = x
        return self.err_code

#------------------------------------------------------------------------------
    def call_fil_method(self, method: str, fc: str = "") -> int:
        """
        Instantiate the filter design class passed  as string ``fc`` with the
        class attribute ``fil_inst``. If ``fc = None``, use the previously
        instantiated filter design class.

        Next, call the design method passed as string ``method`` of the instantiated
        filter design class.

        Parameters
        ----------

        method : string
            The name of the design method to be called (e.g. 'lp_min')

        fc : string (optional, default: None)
            The name of the filter design class to be instantiated. When nothing
            is specified, the last filter selection is used.

        Returns
        -------

        err_code : int
            one of the following error codes:
             :-1: filter design operation has been cancelled by user

             :0: filter design method exists and is callable

             :16: passed method name is not a string

             :17: filter design method does not exist in class

             :18: filter design error containing "order is too high"

             :19: filter design error containing "failure to converge"

             :99: unknown error

        Examples
        --------

        >>> call_fil_method("lp_min", fc="cheby1")

        The example first creates an instance of the filter class 'cheby1' and
        then performs the actual filter design by calling the method 'lp_min'. This
        method reads and stores parameters from / to the filter dictionary.
        """
        if self.err_code >= 16 or self.err_code < 0:
            self.err_code = 0 #  # clear previous method call error
            err_string = ""

        if fc:
            # filter class was part of the argument, (re-)create class instance
            self.err_code = self.create_fil_inst(fc)
            if self.err_code is None:
                logger.warning(
                    "Err_Code is '%s' but should be numeric!", self.err_code)
                self.err_code = 0

        # Error during filter design class instantiation (class fc could not be instantiated)
        if self.err_code > 0:
            err_string = \
                "Filter design class could not be instantiated, see previous error message."

        # Test whether 'method' is a string:
        elif not isinstance(method, str):
            err_string = f"Method name '{method}' is not a string."
            self.err_code = 16

        # Test whether filter class contains passed method
        elif not hasattr(FilterFactory.fil_inst, method):
            err_string = f"Method '{method}' doesn't exist in class "\
                f"'{FilterFactory.fil_inst.__class__.__name__}'."
            self.err_code = 17

        else: # everything ok so far, try calling method
              # err_code = -1 means "operation cancelled"
            try:
                #------------------------------------------------------------------
                # call the actual filter method, results are stored in the filter dict
                self.err_code = getattr(FilterFactory.fil_inst, method)()
                if not isinstance(self.err_code, int):
                    logger.error("self.err_code = '%s' is of type '%s' but should be 'int'!",
                                 str(self.err_code), type(self.err_code).__name__)
                    self.err_code = 0 # assume everything ok if no int returned
                #------------------------------------------------------------------
            except Exception as e:
                err_string =\
                    f"Error in method '{method}' of class "\
                    f"'{type(FilterFactory.fil_inst).__name__}':\n\t{e}"
                if e:
                    err_string += "\n" # add line break at the end of error message
                if "order n is too high" in str(e).lower():
                    self.err_code = 18
                    err_string += "\tTry changing the specifications."
                elif "failure to converge" in str(e).lower():
                    self.err_code = 19
                    err_string += "\tTry changing the specifications."
                else:
                    self.err_code = 99
                logger.error("Err_Code %s: %s", str(self.err_code), err_string)
                debug_exception()

        if self.err_code > 0:
            logger.error("ErrCode %s: %s", self.err_code, err_string)
            debug_exception()

        return self.err_code

#------------------------------------------------------------------------------
# Module instance of FilterFactory():
_fil_factory = FilterFactory()
# accessors
create_fil_inst = _fil_factory.create_fil_inst
call_fil_method = _fil_factory.call_fil_method
def get_fil_inst():
    return _fil_factory.fil_inst
# Usage:
# from filter_factory import create_fil_inst, call_fil_method, get_fil_inst
# create_fil_inst(...)  # test whether class can be instantiated
# call_fil_method(...)  # do the actual method call
# get_fil_inst().ft     # access the 'ft' attribute

######################################################################
if __name__ == '__main__':
    # Run module standalone with `python -m pyfda.filter_factory`

    print("\nAll CFP.FILTER_CLASSES_DICT:\n", CFP.FILTER_CLASSES_DICT.keys())
    print("\nTest 'create_fil_inst:'\n========================")
    print("aaa:", create_fil_inst("aaa")) # class doesn't exist
    print("Cheby1:", create_fil_inst("Cheby1")) # first time inst.
    print("Cheby1:", create_fil_inst("Cheby1")) # second time inst.
    print("Cheby2:", create_fil_inst("Cheby2")) # new class
    print("Cheby2.rt_dict", FilterFactory.fil_inst.rt_dict)

    print("\nTest 'call_fil_method:'\n=======================")
    print("lp_man, fc = Cheby2:",
          call_fil_method("lp_man", fc = "Cheby2"),"\n")
    print("\tLPmax:", call_fil_method("LPmax", fc = "Cheby2")) # doesn't exist
    print("Int 1:", call_fil_method(1, fc = "Cheby2"),"\n") # not a string
    print("lp_min:", call_fil_method("lp_min"),"\n") # changed method

    print("lp_min, fc = Cheby2:", call_fil_method("lp_min", fc = "Cheby2"),"\n")
    print("lp_man, fc = Cheby1:", call_fil_method("lp_man", fc = "Cheby1"))
    print("fil_inst.ft = ", get_fil_inst().ft)
