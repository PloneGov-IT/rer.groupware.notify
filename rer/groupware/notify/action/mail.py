# -*- coding: utf-8 -*-

from Acquisition import aq_inner, aq_parent
from OFS.SimpleItem import SimpleItem
from OFS.interfaces import IApplication

from zope.i18n import translate
from zope.component import adapts
from zope.interface import Interface, implements
from zope.formlib import form
from zope import schema

from plone.app.contentrules.browser.formhelper import AddForm, EditForm
from plone.contentrules.rule.interfaces import IRuleElementData, IExecutable

from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode

from Products.Archetypes.interfaces import IBaseContent
from Products.Archetypes.BaseUnit import BaseUnit

from rer.groupware.notify import messageFactory as _
from rer.groupware.notify import logger
from rer.groupware.room.interfaces import IRoomArea
from rer.groupware.room.interfaces import IGroupRoom

class IMailForGroupwareNotificationAction(Interface):
    """Definition of the configuration available for a mail action
    """
    subject = schema.TextLine(
        title = _(u"Subject"),
        description = _(u"Subject of the message"),
        required = True
        )

    source = schema.TextLine(
        title = _(u"Sender email"),
        description = _(u"The email address that sends the email. If no email is "
                         "provided here, it will use the portal from address."),
         required = False
         )

    message = schema.Text(
        title = _(u"Mail message"),
        description = _('help_message',
                        default=u"Type in here the message that you want to send. Some "
                                 "defined content can be replaced: ${title} will be replaced by the title "
                                 "of the document that raised the event.\n"
                                 "${url} will be replaced by the URL of the item.\n"
                                 "${room_title} will be replaced by the name of the room.\n"
                                 "${room_url} will be replaced by the URL of the room.\n"
                                 "${area_title} will be replaced by the name of the area.\n"
                                 "${area_url} will be replaced by the URL of the area."                                 
                                 ),
        required = True
        )


class MailForGroupwareNotificationAction(SimpleItem):
    """
    The implementation of the action defined before
    """
    implements(IMailForGroupwareNotificationAction, IRuleElementData)

    subject = u''
    message = u''
    source = u''

    element = 'plone.actions.GroupwareMail'

    def __init__(self, area_id=None):
        super(MailForGroupwareNotificationAction, self).__init__()
        self.area_id = area_id

    @property
    def summary(self):
        return _('action_summary',
                 default=u'Groupware notifications')


class MailActionExecutor(object):
    """The executor for this action.
    """
    implements(IExecutable)
    adapts(Interface, IMailForGroupwareNotificationAction, Interface)

    def __init__(self, context, element, event):
        self.context = context
        self.element = element
        self.event = event

    def __call__(self):
        context = self.context
        element = self.element
        event = self.event
        recipients = []      

        mailhost = getToolByName(aq_inner(self.context), "MailHost")
        if not mailhost:
            logger.error('You must have a Mailhost utility to execute this action')
            return False

        source = element.source
        urltool = getToolByName(aq_inner(context), "portal_url")
        mtool = getToolByName(aq_inner(context), "portal_membership")
        portal = urltool.getPortalObject()
        email_charset = portal.getProperty('email_charset')
        if not source:
            # no source provided, looking for the site wide "from" email address
            from_address = portal.getProperty('email_from_address')
            if not from_address:
                logger.error('You must provide a source address for this '
                             'action or enter an email in the portal properties')
                return False
            from_name = portal.getProperty('email_from_name')
            source = "%s <%s>" % (from_name, from_address)

        obj_title = safe_unicode(event.object.Title())
        event_url = event.object.absolute_url()
        parent = self._getParentDocument(aq_inner(event.object))

        # find parent area and room
        area = self._getParentArea(context)
        room = self._getParentRoom(area or context)

        if not mtool.isAnonymousUser():
            member = mtool.getAuthenticatedMember()
            user = member.getProperty('fullname') or member.getId()
        else:
            user = translate(_('Anonymous'), context=context.REQUEST) 

        subject = self.element.subject.replace("${url}", event_url)
        subject = subject.replace("${title}", obj_title)
        subject = subject.replace("${room_title}", room.Title())
        subject = subject.replace("${room_url}", room.absolute_url())
        subject = subject.replace("${user}", user)
        
        if hasattr(event.object, 'text'):
            text = event.object.text
            if isinstance(text, BaseUnit):
                # Ploneabord?
                text = str(text).decode('utf-8')
                transforms = getToolByName(context, 'portal_transforms')
                stream = transforms.convertTo('text/plain', text, mimetype='text/html')
                text = stream.getData().strip() 
            elif not isinstance(text, basestring):
                text = str(text).decode('utf-8')
        elif hasattr(event.object, 'getText'):
            transforms = getToolByName(context, 'portal_transforms')
            text = event.object.getText()
            stream = transforms.convertTo('text/plain', text, mimetype='text/html')
            text = stream.getData().strip()
        else:
            text = ''

        if text:
            # identation
            text = "\n".join(["\t" + l for l in text.splitlines()])

        message = self.element.message.replace("${url}", event_url)
        message = message.replace("${title}", obj_title)
        message = message.replace("${room_title}", room.Title())
        message = message.replace("${room_url}", room.absolute_url())
        message = message.replace("${user}", user)
        message = message.replace("${parent_title}", parent.title_or_id())
        message = message.replace("${text}", text)

        if area:
            subject = subject.replace("${area_title}", area.Title())
            subject = subject.replace("${area_url}", area.absolute_url())
            message = message.replace("${area_title}", area.Title())
            message = message.replace("${area_url}", area.absolute_url())

        recipients = self._notification_recipients(room, area or element.area_id)

        # now tranform recipients in a iterator, if needed
        if type(recipients) == str or type(recipients) == unicode:
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
            if IBaseContent.providedBy(context):
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
        if isinstance(area, basestring):
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
    label = _(u"Add Groupware notification action")
    description = _(u"A mail action for the Groupware suite.")
    form_name = _(u"Configure element")

    def create(self, data):
        a = MailForGroupwareNotificationAction()
        form.applyChanges(a, self.form_fields, data)
        return a


class MailForGroupwareNotificationEditForm(EditForm):
    """
    An edit form for the mail action
    """
    form_fields = form.FormFields(IMailForGroupwareNotificationAction)
    label = _(u"Configure Groupware notification action")
    description = _(u"A mail action for the Groupware suite.")
    form_name = _(u"Configure element")
