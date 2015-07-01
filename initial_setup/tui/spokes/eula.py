"""EULA TUI spoke for the Initial Setup"""

import gettext
import codecs
import logging

from pyanaconda.ui.tui.spokes import NormalTUISpoke
from pyanaconda.ui.tui.simpleline.widgets import TextWidget, CheckboxWidget
from pyanaconda.ui.tui.simpleline.base import UIScreen
from pyanaconda.ui.common import FirstbootOnlySpokeMixIn
from initial_setup.product import get_license_file_name
from initial_setup.common import LicensingCategory

log = logging.getLogger("initial-setup")

_ = lambda x: gettext.ldgettext("initial-setup", x)
N_ = lambda x: x

__all__ = ["EULAspoke"]

class EULAspoke(FirstbootOnlySpokeMixIn, NormalTUISpoke):
    """The EULA spoke providing ways to read the license and agree/disagree with it."""

    title = _("License information")
    category = LicensingCategory

    def __init__(self, *args, **kwargs):
        NormalTUISpoke.__init__(self, *args, **kwargs)

        self._have_eula = True

    def initialize(self):
        NormalTUISpoke.initialize(self)

        self._have_eula = bool(get_license_file_name())

    def refresh(self, args=None):
        NormalTUISpoke.refresh(self, args)

        if self._have_eula:
            log.debug("license found")
            # make the options aligned to the same column (the checkbox has the
            # '[ ]' prepended)
            self._window += [TextWidget("    1) %s" % _("Read the License Agreement")), ""]
            self._window += [CheckboxWidget(title="2) %s" % _("I accept the license agreement."),
                                            completed=self.data.eula.agreed), ""]
        else:
            log.debug("license not found")
            self._window += [TextWidget(_("No license found. Please report this "
                                          "at http://bugzilla.redhat.com")), ""]

    def prompt(self, args=None):
        """Return the default prompt with appended option number.
        It's more intuitive for the user.

        :param args: optional argument passed from switch_screen calls
        :type args: anything

        :return: returns text to be shown next to the prompt for input or None
                 to skip further input processing
        :rtype: str|None
        """
        return _(u"  Please make your choice from above [ '1' to read license | 'q' to quit |\n"
                  "  'c' to continue | 'r' to refresh]: ")

    @property
    def completed(self):
        # Either there is no EULA available, or user agrees/disagrees with it.
        return not self._have_eula or self.data.eula.agreed

    @property
    def mandatory(self):
        # This spoke is always mandatory.
        return True

    @property
    def status(self):
        if not self._have_eula:
            return _("No license found")

        return _("License accepted") if self.data.eula.agreed else _("License not accepted")

    def apply(self):
        # nothing needed here, the agreed field is changed in the input method
        pass

    def input(self, args, key):
        try:
            keyid = int(key)
        except ValueError:
            # only number choices are processed here
            return key

        if keyid == 1:
            # show license
            log.debug("showing the license")
            eula_screen = LicenseScreen(self._app)
            self.app.switch_screen_with_return(eula_screen)
            return None
        elif keyid == 2:
            # toggle EULA agreed checkbox by changing ksdata
            log.debug("license accepted state changed to: %s", self.data.eula.agreed)
            self.data.eula.agreed = not self.data.eula.agreed
            return None

        # some numerical value that cannot be processed here
        return key

class LicenseScreen(UIScreen):
    """Screen showing the License without any input from user requested."""

    # no title needed, we just want to show the license
    title = ""

    def __init__(self, app, screen_height=25):
        UIScreen.__init__(self, app, screen_height)

        self._license_file = get_license_file_name()

    def refresh(self, args=None):
        UIScreen.refresh(self, args)

        # read the license file and make it one long string so that it can be
        # processed by the TextWidget to fit in the screen in a best possible
        # way
        log.debug("reading the license file")
        buf = u""
        with codecs.open(self._license_file, "r", "utf-8", "ignore") as fobj:
            for line in fobj:
                buf += line

        self._window += [TextWidget(buf), ""]

    def prompt(self, args=None):
        # we don't want to prompt user, just close the screen
        self.close()
        return None
