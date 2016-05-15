[loggers]
# List of loggers:
# - root logger has to be present
# - section name is "logger_" + name specified in the keys below. The logger 
#   name is derived automatically in the files-to-be-logged from their
#  __name__ attribute
#
keys=root, pyfdax, filter_tree_builder, hdl_specs, 
    input_tab_widgets, input_specs, input_files, input_freq_specs, input_freq_units,
    plot_tab_widgets

[handlers]
# List of handlers
keys=consoleHandler,fileHandler

[formatters]
# List of formatters
keys=simpleFormatter,noDateFormatter

#===================================================
[logger_root]
level=NOTSET
handlers=consoleHandler

[logger_pyfdax]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.pyfdax
propagate=0

[logger_filter_tree_builder]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.filter_tree_builder
propagate=0
#-------------------- input_widgets -------------------
[logger_input_tab_widgets]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.input_widgets.input_tab_widgets
propagate=0

[logger_input_specs]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.input_widgets.input_specs
propagate=0

[logger_input_files]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.input_widgets.input_files
propagate=0

[logger_input_freq_specs]
level=DEBUG
handlers=fileHandler
qualname=pyfda.input_widgets.input_freq_specs
propagate=0

[logger_input_freq_units]
level=DEBUG
handlers=fileHandler
qualname=pyfda.input_widgets.input_freq_units
propagate=0
#-------------------- plot_widgets ----------------------
[logger_plot_tab_widgets]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.plot_widgets.plot_tab_widgets
propagate=0

#------------------- hdl_generation ---------------------
[logger_hdl_specs]
level=DEBUG
handlers=fileHandler,consoleHandler
qualname=pyfda.hdl_generation.hdl_specs
propagate=0

#------------------------------------------
[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=noDateFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=DynFileHandler # FileHandler is default
level=DEBUG
formatter=simpleFormatter
args=('pyfda.log', 'w') # overwrites log file
#args=('pyfda.log','a') # appends to log file
#-------------------------------------------

[formatter_simpleFormatter]
format=[%(asctime)s.%(msecs).03d] [%(levelname)7s] [%(name)s:%(lineno)s] %(message)s
# for linebreaks simply make one!
datefmt=%Y-%m-%d %H:%M:%S

[formatter_noDateFormatter]
format=[%(levelname)7s] [%(name)s:%(lineno)s] %(message)s

# use "logger.debug(This %s sucks, mystring)" to avoid unneccessary formatting: 
# http://reinout.vanrees.org/weblog/2015/06/05/logging-formatting.html
