import simplejson
import os
import logging


class DataFile:
    def __init__(self, filename, default={}):
        self._filename = filename
        if os.path.exists(filename):
            with open(filename) as f:
                self._data = simplejson.load(f)
        else:
            self._data = dict(default)
        self._original = simplejson.dumps(self._data)

    def data(self):
        return self._data

    def saveIfChanged(self, data):
        if simplejson.dumps(data) == self._original:
            logging.info("Not writing to disk: nothing changed")
            return
        with open(self._filename, "w") as f:
            f.write(simplejson.dumps(data, indent=4, sort_keys=True))
        logging.info("Wrote new data to disk")
