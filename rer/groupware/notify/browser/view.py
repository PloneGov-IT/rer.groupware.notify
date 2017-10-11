# -*- coding: utf-8 -*-
from plone.protect.utils import addTokenToUrl
from plone import api
from plone.memoize import view
from Products.Five.browser import BrowserView
from rer.groupware.notify import messageFactory as _
from rer.groupware.room.interfaces import IRoomArea
from zExceptions import Unauthorized
from zope.i18n import translate
from plone.api.exc import GroupNotFoundError
import json
from zope.i18n import translate


class RERGroupwareNotifySupportView(BrowserView):

    @property
    @view.memoize
    def member(self):
        return api.user.get_current()

    @property
    @view.memoize
    def member_groups(self):
        return self.member.getGroups()

    @view.memoize
    def _getContainerRoom(self):
        for parent in self.context.aq_inner.aq_chain:
            if getattr(parent, 'portal_type', '') == 'GroupRoom':
                return parent
        return None

    @property
    def room(self):
        return self._getContainerRoom()

    def listNotificationGroups(self):
        """List of groups related to area notifications"""
        room = self.room
        if not room:
            # I'm not in a room or subtree and the portlet will not be
            # visible
            return {}
        room_id = room.getId()
        # now I need all area inside

        areas = api.content.find(
            object_provides=IRoomArea,
            path={'query': '/'.join(room.getPhysicalPath()), 'depth': 1},
            sort_on='getObjPositionInParent'
        )
        groups = []
        for area in areas:
            if area.exclude_from_nav:
                # if an area is hidden, we don't show it in notify portlet
                continue
            area_data = {
                'id': area.getId,
                'title': area.Title
            }
            group_id = "{}.{}.notify".format(room_id, area.getId)
            group = api.group.get(group_id)
            if group:
                area_data['subscribed'] = self.inNotificationGroup(
                    group_id)
                area_data['group_data'] = {
                    'id': group_id,
                    'title': group.getProperty('title') or group_id
                }
            groups.append(area_data)

        # other, not area related, groups
        group_id = "{}.comments.notify".format(room_id)
        comments_group = api.group.get(group_id)
        if comments_group:
            groups.append({
                'id': 'comments',
                'title': translate(_(u'Comments'), context=self.request),
                'subscribed': self.inNotificationGroup(group_id),
                'group_data': {
                    'id': group_id,
                    'title': comments_group.getProperty('title') or group_id
                }
            })
        return {
            'room': room.Title(),
            'groups': groups
        }

    def inNotificationGroup(self, group_id):
        return group_id in self.member_groups

    def generateUrl(self, group_id):
        url = '{}/notification-subscription?group_id={}'.format(self.context.absolute_url(), group_id)
        return addTokenToUrl(url)


class NotificationSubscriptionView(RERGroupwareNotifySupportView):

    """Manage subscription to notification groups"""

    def __call__(self, *args, **kwargs):
        request = self.request
        group_id = request.form.get('group_id')
        self.request.response.setHeader("Content-type", "application/json")
        if not group_id:
            message = _(
                'add_notify_nogroup_error',
                default=u"Group not given. unable to execute the operation.")
            return json.dumps({
                'status': 'error',
                'message': translate(message, context=self.request),
            })
        member = api.user.get_current()
        self._checkSecurity(member)
        userid = member.getId()
        fullname = member.getProperty('fullname') or userid
        try:
            group_members = api.user.get_users(groupname=group_id)
        except GroupNotFoundError:
            message = _(
                'add_notify_group_error',
                default=u"Group ${group_id} not found. unable to execute the operation.",
                mapping={'user': fullname})
            return json.dumps({
                'status': 'error',
                'message': translate(message, context=self.request),
            })
        if member not in group_members:
            api.group.add_user(groupname=group_id, user=member)
            message = _(
                'added_to_notify_group',
                default=u"User ${user} added to notification group",
                mapping={'user': fullname})
            subscribed = True
        else:
            api.group.remove_user(groupname=group_id, user=member)
            message = _(
                'removed_from_notify_group',
                default=u"User ${user} removed from notification group",
                mapping={'user': fullname})
            subscribed = False
        return json.dumps({
            'status': 'ok',
            'message': translate(message, context=self.request),
            'group_id': group_id,
            'subscribed': subscribed
        })

    def _checkSecurity(self, member, raiseOnUnauth=True):
        """If the user is not a poweruser, we need to check if he can really subscribe to the notification group.
        i.e: is part of the room?
        """
        if member.has_permission('rer.groupware.notify: Manage notification settings', self.context):
            return True
        # BBB: checking by role?
        if 'Active User' in member.getRolesInContext(self.context):
            return True
        if raiseOnUnauth:
            raise Unauthorized('You are not part of the room')
        return False
