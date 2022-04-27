# -*- coding: utf-8 -*-
from Acquisition import aq_inner, aq_parent
from OFS.interfaces import IApplication
from OFS.SimpleItem import SimpleItem

from plone import api

from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from plone.contentrules.rule.interfaces import IRuleElementData, IExecutable
from plone.stringinterp.interfaces import IStringInterpolator

from plone.dexterity.interfaces import IDexterityContent

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

from rer.groupware.notify import logger
from rer.groupware.notify import messageFactory as _
from rer.groupware.room.interfaces import IGroupRoom
from rer.groupware.room.interfaces import IRoomArea

from zope import schema
from zope.component import adapts
from zope.formlib import form
from zope.i18n import translate

from zope.interface import Interface, implementer


class IMailForGroupwareNotificationAction(Interface):
    """Definition of the configuration available for a mail action
    """
    subject = schema.TextLine(
        title=_("Subject"),
        description=_("Subject of the message"),
        required=True
        )

    source = schema.TextLine(
        title=_("Sender email"),
        description=_("The email address that sends the email. If no email is "
                      "provided here, it will use the portal from address."),
         required=False
         )

    message = schema.Text(
        title=_("Mail message"),
        description=_('help_message',
                        default= "Type in here the message that you want to send. Some "
                                 "defined content can be replaced: ${title} will be replaced by the title "
                                 "of the document that raised the event.\n"
                                 "${url} will be replaced by the URL of the item.\n"
                                 "${room_title} will be replaced by the name of the room.\n"
                                 "${room_url} will be replaced by the URL of the room.\n"
                                 "${area_title} will be replaced by the name of the area.\n"
                                 "${area_url} will be replaced by the URL of the area."
                                 ),
        required=True
        )


@implementer(IMailForGroupwareNotificationAction, IRuleElementData)
class MailForGroupwareNotificationAction(SimpleItem):
    """
    The implementation of the action defined before
    """

    subject = ''
    message = ''
    source = ''

    element = 'plone.actions.GroupwareMail'

    def __init__(self, area_id=None):
        super(MailForGroupwareNotificationAction, self).__init__()
        self.area_id = area_id

    @property
    def summary(self):
        return _('action_summary',
                 default='Groupware notifications')


@implementer(IExecutable)
class MailActionExecutor(object):
    """The executor for this action.
    """

    adapts(Interface, IMailForGroupwareNotificationAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        context = self.context
        element = self.element
        event = self.event
        obj = event.object
        recipients = []
        interpolator = IStringInterpolator(obj)

        mailhost = getToolByName(aq_inner(self.context), "MailHost")
        if not mailhost:
            logger.error('You must have a Mailhost utility to execute this action')
            return False

        source = element.source
        mtool = getToolByName(aq_inner(context), "portal_membership")
        email_charset = api.portal.get_registry_record('plone.email_charset')
        if not source:
            # no source provided, looking for the site wide "from" email address
            from_address = api.portal.get_registry_record('plone.email_from_address')
            if not from_address:
                logger.error('You must provide a source address for this '
                             'action or enter an email in the portal properties')
                return False
            from_name = api.portal.get_registry_record('plone.email_from_name')
            source = "%s <%s>" % (from_name, from_address)

        # obj_title = safe_unicode(obj.Title())
        # event_url = obj.absolute_url()
        parent = self._getParentDocument(aq_inner(obj))
        # find parent area and room
        area = self._getParentArea(context)
        room = self._getParentRoom(area or context)

        if not mtool.isAnonymousUser():
            member = mtool.getAuthenticatedMember()
            user = member.getProperty('fullname') or member.getId()
        else:
            user = translate(_('Anonymous'), context=context.REQUEST)

        subject = interpolator(self.element.subject)

        subject = subject.replace("${room_title}", room.Title())
        subject = subject.replace("${room_url}", room.absolute_url())
        subject = subject.replace("${user}", user)

        # prepend interpolated message with \n to avoid interpretation
        # of first line as header
        message = "\n%s" % interpolator(self.element.message)

        message = message.replace(
            "${room_title}",
            room.Title()
        )
        message = message.replace("${room_url}", room.absolute_url())
        message = message.replace("${user}", user)
        if parent:
            message = message.replace(
                "${parent_title}",
                parent.title_or_id()
            )

        if area:
            subject = subject.replace("${area_title}", area.Title())
            subject = subject.replace("${area_url}", area.absolute_url())
            message = message.replace("${area_title}", area.Title())
            message = message.replace("${area_url}", area.absolute_url())

        recipients = self._notification_recipients(room, area or element.area_id)

        # now tranform recipients in a iterator, if needed
        if type(recipients) == str:
            recipients = [str(recipients),]

        for email_recipient in [r for r in recipients if r]:
            logger.debug('sending to: %s' % email_recipient)

            try: # sending mail in Plone 4
                mailhost.send(message, mto=email_recipient, mfrom=source,
                              subject=subject, charset=email_charset)
            except: #sending mail in Plone 3
                mailhost.secureSend(message, email_recipient, source,
                                    subject=subject, subtype='plain',
                                    charset=email_charset, debug=False,
                                    From=source)

        return True

    def _getParentDocument(self, context):
        """Return the parent document (in case of comments)"""
        while True:
            if IDexterityContent.providedBy(context):
                return context
            if IApplication.providedBy(context):
                return None
            context = aq_parent(context)

    def _getParentArea(self, context):
        while True:
            if IRoomArea.providedBy(context):
                break
            context = aq_parent(aq_inner(context))
            if IApplication.providedBy(context):
                return None
        return context

    def _getParentRoom(self, context):
        while True:
            if IGroupRoom.providedBy(context):
                break
            context = aq_parent(aq_inner(context))
            if IApplication.providedBy(context):
                return None
        return context

    def _notification_recipients(self, room, area):
        acl_users = getToolByName(self.context, 'acl_users')
        if isinstance(area, str):
            group = acl_users.getGroupById(room.getId()+'.' + area + '.notify')
        else:
            group = acl_users.getGroupById(room.getId()+'.' + area.getId() + '.notify')
        if group:
            for member in group.getGroupMembers():
                yield member.getProperty('email')


class MailForGroupwareNotificationAddForm(AddForm):
    """
    An add form for the mail action
    """
    form_fields = form.FormFields(IMailForGroupwareNotificationAction)
    label = _("Add Groupware notification action")
    description = _("A mail action for the Groupware suite.")
    form_name = _("Configure element")

    def create(self, data):
        a = MailForGroupwareNotificationAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class MailForGroupwareNotificationEditForm(EditForm):
    """
    An edit form for the mail action
    """
    form_fields = form.FormFields(IMailForGroupwareNotificationAction)
    label = _("Configure Groupware notification action")
    description = _("A mail action for the Groupware suite.")
    form_name = _("Configure element")
