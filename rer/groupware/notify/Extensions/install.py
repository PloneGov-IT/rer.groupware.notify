# -*- coding: utf-8 -*-
from zope.component import getUtility, queryUtility
from plone.contentrules.engine.interfaces import IRuleStorage
from rer.groupware.notify.action.mail import MailForGroupwareNotificationAction

from rer.groupware.notify import logger

def install(portal):
    setup_tool = portal.portal_setup
    setup_tool.runAllImportStepsFromProfile('profile-rer.groupware.notify:default')


def uninstall(portal, reinstall=False):
    if not reinstall:
        removeRules(portal)
        setup_tool = portal.portal_setup
        setup_tool.runAllImportStepsFromProfile('profile-rer.groupware.notify:uninstall')


def removeRules(portal):
    storage = getUtility(IRuleStorage)
    for rule_id, rule in storage.items():
        for action in rule.actions:
            if isinstance(action, MailForGroupwareNotificationAction):
                logger.info("[REMOVED RULE] - %s" % rule.title)
                del storage[rule_id]
