# -*- coding: utf-8 -*-

from zope.interface import implements

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.CMFCore.utils import getToolByName
from plone.memoize.instance import memoize

from plone.portlets.interfaces import IPortletDataProvider
from plone.app.portlets.portlets import base

from rer.groupware.notify import messageFactory as _
from rer.groupware.room.interfaces import IRoomArea

class IGroupsNotificationPortlet(IPortletDataProvider):
    """
    Portlet per eseguire iscruzioni alle notifiche
    """

class Assignment(base.Assignment):
    """Portlet assignment.

    This is what is actually managed through the portlets UI and associated
    with columns.
    """
    
    implements(IGroupsNotificationPortlet)

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
        
        self.room_title = ''
        self.room_id = ''
            
    render = ViewPageTemplateFile('groups_notification_portlet.pt')
    
    @property
    def available(self):
        pm = getToolByName(self.context,'portal_membership')
        if pm.isAnonymousUser():
            return False
        if not self.listNotificationGroups():
            return False
        return True

    @property
    @memoize
    def member(self):
        portal_membership = getToolByName(self.context, 'portal_membership')
        return portal_membership.getAuthenticatedMember()

    def listNotificationGroups(self):
        room = None
        for parent in self.context.aq_inner.aq_chain:
            if getattr(parent,'portal_type','') == 'GroupRoom':
                room = parent
        if not room:
            # I'm not in a room or subtree and the portlet will not be visible
            return []
        self.room_title = room.Title()
        self.room_id = room.getId()
        
        # now I need all area inside
        catalog = getToolByName(self.context, 'portal_catalog')
        areas = catalog(object_provides=IRoomArea.__identifier__,
                        path={'query': '/'.join(room.getPhysicalPath()), 'depth': 1},
                        sort_on='getObjPositionInParent')
        room_areas = []
        acl_users = getToolByName(self.context, 'acl_users')
        notify_groups = [g for g in acl_users.getGroups() \
                    if g.getId().startswith("%s." % self.room_id) and g.getId().endswith(".notify")]
        for area in areas:
            area_data = {}
            area_data['id'] = area.getId
            area_data['title'] = area.Title
            area_data['groups'] = [{'id': g.getId(),
                                    'title': g.getProperty('title')} for g in notify_groups \
                        if g.getId().startswith("%s.%s." % (self.room_id, area.getId))]
            room_areas.append(area_data)
        return room_areas
    
    def inNotificationGroup(self, group):
        return group.get('id') in self.member.getGroups()


        
class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()
