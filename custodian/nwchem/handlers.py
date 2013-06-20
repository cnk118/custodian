#!/usr/bin/env python

"""
TODO: Change the module doc.
"""

from __future__ import division

__author__ = "Shyue Ping Ong"
__version__ = "0.1"
__maintainer__ = "Shyue Ping Ong"
__email__ = "shyuep@gmail.com"
__status__ = "Beta"
__date__ = "5/20/13"

import shutil
import time

from custodian.custodian import ErrorHandler
from pymatgen.serializers.json_coders import MSONable
from pymatgen.io.nwchemio import NwOutput


class NwchemErrorHandler(ErrorHandler, MSONable):
    """
    Error handler for Nwchem Jobs. Currently tested only for B3LYP DFT jobs.
    """

    def __init__(self, output_filename="mol.nwout"):
        self.output_filename = output_filename

    def check(self):
        # Checks output file for errors.
        out = NwOutput(self.output_filename)
        self.errors = []
        self.input_file = out.job_info['input']
        if out.data[-1]["has_error"]:
            self.errors.extend(out.data[-1]["errors"])
        self.errors = list(set(self.errors))
        return len(self.errors) > 0

    def _mod_input(self, search_string_func, mod_string_func):
        with open(self.input_file) as f:
            lines = []
            for l in f:
                if search_string_func(l):
                    lines.append(mod_string_func(l))
                else:
                    lines.append(l)

        with open(self.input_file, "w") as fout:
            fout.write("".join(lines))

    def correct(self):
        #Right now, only fixes autoz error.
        actions = []
        for e in self.errors:
            if e == "autoz error":
                #Hackish solution for autoz error.
                self._mod_input(
                    lambda l: l.lower().strip().startswith("geometry"),
                    lambda l: "{} noautoz\n".format(l.strip()))
                actions.append("Set noautoz to geometry.")
            elif e == "Bad convergence":
                #Hackish solution for bad convergence error. Set cgmin.
                self._mod_input(
                    lambda l: l.lower().strip() == "dft",
                    lambda l: "{}\n cgmin\n".format(l.strip()))
                actions.append("Set cgmin.")
            else:
                # For unimplemented errors, this should just cause the job to
                # die.
                return {"errors": self.errors, "actions": None}
        return {"errors": self.errors, "actions": actions}

    @property
    def is_monitor(self):
        return False

    def __str__(self):
        return "NwchemErrorHandler"

    @property
    def to_dict(self):
        return {"@module": self.__class__.__module__,
                "@class": self.__class__.__name__,
                "output_filename": self.output_filename}

    @classmethod
    def from_dict(cls, d):
        return cls(d["output_filename"])
