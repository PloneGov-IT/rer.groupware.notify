# -*- coding: utf-8 -*-

import logging
from zope.i18nmessageid import MessageFactory

logger = logging.getLogger('rer.groupware.notify')
messageFactory = MessageFactory('rer.groupware.notify')

def initialize(context):
    """Initializer called when used as a Zope 2 product."""
