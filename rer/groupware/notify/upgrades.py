# -*- coding: utf-8 -*-
from rer.groupware.notify import logger

default_profile = 'profile-rer.groupware.notify:default'


def to_2000(context):
    """
    Add e new registry field
    """
    logger.info('Upgrading rer.groupware.notify to version 1.6.0')
    context.runImportStepFromProfile(default_profile, 'plone.app.registry')
    logger.info('Reinstalled registry')
