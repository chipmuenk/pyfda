# -*- coding: utf-8 -*-
#
# This file is part of the pyFDA project hosted at https://github.com/chipmuenk/pyfda
#
# Copyright © pyFDA Project Contributors
# Licensed under the terms of the MIT License
# (see file LICENSE in root directory for details)

"""
Dummy / template file for manual filter designs by entering P/Z or b/a.
Targets for LP, HP, BP, BS are provided.
Returns nothing.

Attention:
This class is re-instantiated dynamically everytime the filter design method
is selected, calling the __init__ method.

API version info:
    :1.0: initial working release

    :1.1: mark private methods as private

    :1.2: new API using fil_save

    :1.3: new public methods destruct_ui + construct_ui (no longer called by __init__)

    :1.4: module attribute `filter_classes` contains class name and combo box name
         instead of class attribute `name`

    :2.0: Specify the parameters for each subwidget as tuples in a dict where the
         first element controls whether the widget is visible and / or enabled.
         This dict is now called self.rt_dict. When present, the dict self.rt_dict_add
         is read and merged with the first one.

    :2.1: Remove empty methods construct_ui and destruct_ui and attributes
         self.wdg and self.hdl

    :2.2: Rename `filter_classes` -> `classes`, remove Py2 compatibility
"""

__version__ = "2.2"

 #: Dict containing class name : display name
classes = {'Manual_FIR':'Manual', 'Manual_IIR':'Manual'}

FRMT = 'ba' # default output format of filter design routines 'zpk' / 'ba' / 'sos'
has_ui = False #: Flag whether the filter class has a UI or not

msg_man = ('a', "Design the filter using the P/Z or the b/a widget. "
                "The target specs are only used for entering and displaying spec limits.")

info_str =\
"""
**Manual Filter Design**

Manual filter design mode is selected automatically when entering / editing
poles and zeros ("P/Z" tab) or coefficients ("b,a" tab). Use the info tab
or the magnitude frequency response (select "Show Specs") to check whether
the designed filter fulfills the target specs.
"""

class Manual_FIR():
    """
    Dummy filter design class, used / displayed when coefficients or P/Z have
    been entered manually.
    """

    def __init__(self):

        # This part contains static information for building the filter tree

        self.ft = 'FIR'

        self.rt_dict = {
            'COM':{'man':{'fo': ('d', 'N'),
                          'msg': msg_man}
                        },
            'LP': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB'),
                                           'amp':('u','A_PB','A_SB')})
                         }},
            'HP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB'),
                                           'amp':('u','A_SB','A_PB')})
                        }},
            'BS': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2', 'F_PB2'),
                                           'amp':('u','A_PB','A_SB','A_PB2')})
                        }},
            'BP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'HIL': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'DIFF': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }}
                   }

        self.info = info_str
        self.info_doc = []
        self.info_doc.append('manual FIR\n==========')

    #------------------- end of static info for filter tree -------------------

    # def _get_params(self, fil_dict):
    #     """
    #     Translate parameters from the filter dictionary to instance
    #     parameters, scaling / transforming them if needed.
    #     """
    #     self.N     = fb_get('N')
    #     self.F_PB  = fb_get('F_PB')
    #     self.F_SB  = fb_get('F_SB')
    #     self.F_PB2 = fb_get('F_PB2')
    #     self.F_SB2 = fb_get('F_SB2')
    #     self.F_C   = fb_get('F_C')
    #     self.F_C2  = fb_get('F_C2')

    #     self.A_PB  = fb_get('A_PB')
    #     self.A_PB2 = fb_get('A_PB2')
    #     self.A_SB  = fb_get('A_SB')
    #     self.A_SB2 = fb_get('A_SB2')

    def LPman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def HPman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def BPman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def BSman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def HILman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def DIFFman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

#############################################################################
class Manual_IIR():
    """
    Dummy filter design class, used / displayed when coefficients or P/Z have
    been entered manually.
    """
    def __init__(self):

        # This part contains static information for building the filter tree

        self.ft = 'IIR'

        self.rt_dict = {
            'COM':{'man':{'fo': ('d', 'N'),
                          'msg': msg_man}
                        },
            'LP': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB'),
                                           'amp':('u','A_PB','A_SB')})
                         }},
            'HP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB'),
                                           'amp':('u','A_SB','A_PB')})
                        }},
            'BS': {'man':{'tspecs': ('u', {'frq':('u','F_PB','F_SB','F_SB2', 'F_PB2'),
                                           'amp':('u','A_PB','A_SB','A_PB2')})
                        }},
            'BP': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'HIL': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }},
            'DIFF': {'man':{'tspecs': ('u', {'frq':('u','F_SB','F_PB','F_PB2','F_SB2',),
                                           'amp':('u','A_SB','A_PB','A_SB2')})
                        }}
                   }

        self.info = info_str
        self.info_doc = []
        self.info_doc.append('manual IIR\n==========')

        #------------------- end of static info for filter tree ---------------

    # def _get_params(self):
    #     """
    #     Translate parameters from the passed dictionary to instance
    #     parameters, scaling / transforming them if needed.
    #     """
    #     self.N     = fb_get('N')
    #     self.F_PB  = fb_get('F_PB')
    #     self.F_SB  = fb_get('F_SB')
    #     self.F_PB2 = fb_get('F_PB2')
    #     self.F_SB2 = fb_get('F_SB2')
    #     self.F_C   = fb_get('F_C')
    #     self.F_C2  = fb_get('F_C2')

    #     self.A_PB  = fb_get('A_PB')
    #     self.A_PB2 = fb_get('A_PB2')
    #     self.A_SB  = fb_get('A_SB')
    #     self.A_SB2 = fb_get('A_SB2')


    def LPman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def HPman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def BPman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def BSman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def HILman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """

    def DIFFman(self):
        """ Dummy method, to display widgets corresponding to filter type in UI """


#------------------------------------------------------------------------------
if __name__ == '__main__':
    # Run module standalone using "python -m pyfda.filter_widgets.manual"
    from pyfda.filterbroker import fb_get

    filt = Manual_IIR()    # instantiate filter
    filt.LPman()  # design a low-pass with parameters from global dict
    print(fb_get(FRMT)) # return results in default format

    filt = Manual_FIR()    # instantiate filter
    filt.LPman()  # design a low-pass with parameters from global dict
    print(fb_get(FRMT)) # return results in default format
