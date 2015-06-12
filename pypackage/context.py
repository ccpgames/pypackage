"""Context managers to handle the creation and of setuptools required files."""


import os


class SetupContext(object):
    """Context manager for writing and (maybe) removing the setup.py.

    Args::

        config: `pypackage.config.Config` object for the package
        options: `pypackage.Options` object of cmd line flags
    """

    def __init__(self, config, options):
        self.config = config
        self.options = options

    def __enter__(self):
        """Write the setup.py to include it in the build."""

        # dump the config out as a setup.py for back-compat...
        # it's not actually used this build, we pass kwargs directly
        with open("setup.py", "w") as opensetup:
            opensetup.write("{}\n".format(str(self.config)))

        return self

    def __exit__(self, *args):
        """Cleans up the setup.py unless interactive, or -m/-s flags."""

        if not any([self.options.interactive, self.options.metadata,
                    self.options.setup]):
            os.remove("setup.py")


class ManifestContext(object):
    """Context manager to write the MANIFEST.in file if required.

    Args::

        config: `pypackage.config.Config` object for the package
        options: `pypackage.Options` object of cmd line flags
    """

    def __init__(self, config, options):
        self.config = config
        self.options = options
        self._clean = False  # clean up on exit?
        # gather any previously existing entries..
        try:
            with open("MANIFEST.in", "r") as openmanifest:
                self.previously_existing = openmanifest.read().splitlines()
        except:
            self.previously_existing = []

    def __enter__(self):
        """Write the MANIFEST.in file if there are data files in use."""

        keys = ["package_data", "data_files"]
        if not any([getattr(self.config, key, None) for key in keys]):
            return self  # nothing to do

        add_to_manifest = []
        for _, files in getattr(self.config, "package_data", {}).items():
            for file_ in files:
                include_line = "include {}".format(file_)
                if include_line not in self.previously_existing:
                    add_to_manifest.append(include_line)

        for _, files in getattr(self.config, "data_files", []):
            for file_ in files:
                include_line = "include {}".format(file_)
                if include_line not in self.previously_existing:
                    add_to_manifest.append(include_line)

        if add_to_manifest:
            self._clean = True
            with open("MANIFEST.in", "a") as openmanifest:
                openmanifest.write("{}\n".format("\n".join(add_to_manifest)))

        return self

    def __exit__(self, *args):
        if self.previously_existing:
            with open("MANIFEST.in", "w") as openmanifest:
                openmanifest.write("\n".join(self.previously_existing))
        elif self._clean and not (self.options.metadata or self.options.setup):
            os.remove("MANIFEST.in")
