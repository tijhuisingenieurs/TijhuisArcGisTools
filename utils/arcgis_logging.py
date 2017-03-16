import logging


class ArcGisHandler(logging.Handler):

    def __init__(self, arcpy, *args, **kwargs):
        logging.Handler.__init__(self, *args, **kwargs)

        # add references, because this somehow does not work directly,
        # something with the scope of the emit function (does this exists
        # in Python?)
        self.addmessage_ref = arcpy.AddMessage
        self.addwarning_ref = arcpy.AddWarning
        self.adderror_ref = arcpy.AddError

        self.logging_ref = logging

    def emit(self, record):
        msg = self.format(record)

        if record.levelno >= self.logging_ref.ERROR:
            self.adderror_ref(msg)
        elif record.levelno >= self.logging_ref.WARNING:
            self.addwarning_ref(msg)
        else:
            self.addmessage_ref(msg)

def setup_logging(arcpy):

    log = logging.getLogger('')
    log.handlers = []

    ql = ArcGisHandler(arcpy)
    ql.setLevel(logging.DEBUG)

    # fh = logging.FileHandler('plugin_log.log')
    # fh.setLevel(logging.WARNING)

    st = logging.StreamHandler()
    st.setLevel(logging.DEBUG)

    format = logging.Formatter('%(name)-10s - %(levelname)-8s - %(message)s')
    # fh.setFormatter(format)
    st.setFormatter(format)

    log.addHandler(ql)
    # log.addHandler(fh)
    log.addHandler(st)

    return