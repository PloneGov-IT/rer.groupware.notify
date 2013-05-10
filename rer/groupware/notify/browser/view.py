# -*- coding: utf-8 -*-

from zExceptions import Unauthorized

from Products.Five.browser import BrowserView
from Products.CMFCore.utils import getToolByName

from Products.CMFCore import permissions

from rer.groupware.notify import messageFactory as _

class NotificationSubscriptionView(BrowserView):
    """Manage subscription to notification groups"""
    
    def __call__(self, *args, **kwargs):
        request = self.request
        if request.form.get('room_id') and request.form.get('area_id'):
            room_id = request.form.get('room_id')
            area_id = request.form.get('area_id')
            member = getToolByName(self.context, 'portal_membership').getAuthenticatedMember()
            self._checkSecurity(member, room_id)
            portal_groups = getToolByName(self.context, 'portal_groups')
            group_id = '%s.%s.notify' % (room_id, area_id)
            group = portal_groups.getGroupById(group_id)
            group_members = group.getMemberIds()
            userid = member.id
            if userid not in group_members:
                portal_groups.addPrincipalToGroup(userid, group_id)
            else:
                portal_groups.removePrincipalFromGroup(userid, group_id)
            getToolByName(self.context, 'plone_utils').addPortalMessage(_(u'Notification settings changed'))
        request.response.redirect(self.context.absolute_url())
    
    def _checkSecurity(self, member, room_id):
        """If the user is not a poweruser, we need to check if he can really subscribe to the notification group.
        i.e: is part of the room?
        """
        if member.has_permission(permissions.ManagePortal, self.context):
            return True
        if '%s.members' % room_id in member.getGroups():
            return True
        raise Unauthorized('You are not part of the room')
