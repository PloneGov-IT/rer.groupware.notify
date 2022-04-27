# -*- coding: utf-8 -*-
from time import time

from plone.protect.utils import addTokenToUrl

from Acquisition import aq_inner

from plone import api
from plone.app.portlets.portlets import base
from plone.memoize import ram
from plone.memoize.instance import memoize
from plone.portlets.interfaces import IPortletDataProvider

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from rer.groupware.notify import messageFactory as _
from rer.groupware.room.interfaces import IRoomArea

from zope.component import getMultiAdapter
from zope.i18n import translate

from zope.interface import implementer


def _notifylistcache(method, self):
    """
    method for ramcache that store subscriptions list
    """
    context = aq_inner(self.context)
    portal_state = getMultiAdapter(
        (context, self.request), name='plone_portal_state')
    member = portal_state.member()
    room = self._getContainerRoom()
    timestamp = time() // (60 * 60 * 1)
    return (timestamp, member.getId(), room.UID())


class IGroupsNotificationPortlet(IPortletDataProvider):

    """
    Portlet per eseguire iscruzioni alle notifiche
    """

@implementer(IGroupsNotificationPortlet)
class Assignment(base.Assignment):

    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """

    @property
    def title(self):
        return _("Groupware Notifications")


class Renderer(base.Renderer):

    def __init__(self, context, request, view, manager, data):
        self.context = context
        self.request = request
        self.view = view
        self.__parent__ = view
        self.manager = manager
        self.data = data

    render = ViewPageTemplateFile('groups_notification_portlet.pt')

    @property
    def available(self):
        if api.user.is_anonymous():
            return False
        # no portlet for top level acl_users
        acl_users = getToolByName(self.context, 'acl_users')
        if not acl_users.searchUsers(id=self.member.getId()):
            return False
        # checking security: can't subscribe if I'm not member of the room
        user_roles = api.user.get_roles(user=self.member, obj=self.context)
        if 'Active User' not in user_roles:
            return False
        if not self.listNotificationGroups():
            return False
        return True

    @property
    @memoize
    def member(self):
        return api.user.get_current()

    # @memoize
    # def _getContainerRoom(self):
    #     room = None
    #     for parent in self.context.aq_inner.aq_chain:
    #         if getattr(parent, 'portal_type', '') == 'GroupRoom':
    #             room = parent
    #     return room
    #
    # @property
    # def room(self):
    #     return self._getContainerRoom()

    # @ram.cache(_notifylistcache)
    def listNotificationGroups(self):
        """List of groups related to area notifications"""
        view = api.content.get_view(
            name='notify-support-view',
            context=self.context,
            request=self.context.REQUEST,
        )
        if not view:
            return {}
        return view.listNotificationGroups()

    def generateUrl(self, group_id):
        url = '{}/notification-subscription?group_id={}'.format(self.context.absolute_url(), group_id)
        return addTokenToUrl(url)


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
