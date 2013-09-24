# -*- coding: utf-8 -*-

from Acquisition import aq_inner, aq_parent

from zope.i18n import translate
from zope.component import getUtility, queryUtility
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.app.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent
#from zope.app.container.interfaces import INameChooser

from Products.CMFCore.utils import getToolByName

from plone.contentrules.engine.assignments import RuleAssignment
from plone.contentrules.engine.interfaces import IRuleAssignmentManager
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.app.contentrules.conditions.portaltype import PortalTypeCondition
from plone.app.contentrules.rule import Rule, get_assignments
from plone.registry.interfaces import IRegistry

from rer.groupware.room.interfaces import IRoomArea
from rer.groupware.room.interfaces import IGroupRoom

from rer.groupware.notify import logger
from rer.groupware.notify import messageFactory as _
from rer.groupware.notify.interfaces import IGroupwareNotifySettings
from rer.groupware.notify.action.mail import MailForGroupwareNotificationAction


class CreateNotificationGroupsEvent:
    """Create notification groups:
    
    For every Area inside this Room we will create a notification group
    """
    
    def __init__(self, context, event):
        self.context = context
        self.event = event
        self.createAreaGroups()
        self.createCommentGroup()
    
    def createAreaGroups(self):
        context = self.context
        groups_tool = getToolByName(context,'portal_groups')
        catalog = getToolByName(context, 'portal_catalog')

        room_id = context.getId()
        room_title = context.Title()
        results = catalog(object_provides=IRoomArea.__identifier__)

        for brain in results:
            area = brain.getObject()
            group_id = '%s.%s.notify' % (room_id, area.getId())
            if not groups_tool.getGroupById(group_id):
                groups_tool.addGroup(id=group_id,
                                     title=translate(_('notify_group_comment_id',
                                                       default=u"${room_title} ${area_title} Notifications",
                                                       mapping={"room_title" : room_title.decode('utf-8'),
                                                                "area_title" : area.Title(),}),
                                                       context=context.REQUEST))
                logger.info('Created group %s' % group_id)
            else:
                logger.info('Group %s found: skipping' % group_id)

    def createCommentGroup(self):
        context = self.context
        groups_tool = getToolByName(context,'portal_groups')

        room_id = context.getId()
        room_title = context.Title()
        group_id = '%s.comments.notify' % room_id  
        if not groups_tool.getGroupById(group_id):
            groups_tool.addGroup(id=group_id,
                                 title=translate(_(u"${room_title} comments notifications",
                                                   mapping={"room_title" : room_title.decode('utf-8')}),
                                                   context=context.REQUEST))
            logger.info('Created group %s' % group_id)
        else:
            logger.info('Group %s found: skipping' % group_id)


class CreateNotificationRulesEvent(object):
    """
    Create 3 content rules (add, edit, and delete) with the new Groupware action.
    Enable the rule on every area in the room.
    
    Create also the global notification group for comments
    """
    
    def __init__(self, context, event):
        self.context = context
        self.event = event
        self.createAreaRules()
        self.createCommentRule()

    def _getParentRoom(self, context):
        path = None
        while path != '/':
            if IGroupRoom.providedBy(context):
                break
            context = aq_parent(aq_inner(context))
            path = '/'.join(context.getPhysicalPath())
        return context

    def createCommentRule(self):
        context = self.context

        subject=translate(_('notify_subj_comments',
                             default=u'[${room_title}] New comment',
                             mapping={"room_title" : context.Title().decode('utf-8')}),
                          context=context.REQUEST)
        message=translate(_('notify_msg_comments',
                            default=u'A new comment has been added by ${user} to document ${parent_title}.\n'
                                    u'\n'
                                    u'${text}\n'
                                    u'\n'
                                    u'You can click on the following link to see the comment:\n'
                                    u'${url}'),
                          context=context.REQUEST)
        rule_title = translate(_('notify_title_comments',
                                 default=u'[${room_title}] notify for new comments',
                                 mapping={"room_title" : context.Title().decode('utf-8')}),
                               context=context.REQUEST)
        rule_description = translate(_('notify_description_comments',
                                       default=u'All users inside the comments notification group of the room '
                                               u'will be mailed when new comments are added'),
                                     context=context.REQUEST)

        room = self._getParentRoom(context)
        self.createRule(context, room, rule_id="%s-comments" % context.getId(), rule_title=rule_title,
                        rule_description=rule_description, rule_event=IObjectAddedEvent,
                        subject=subject, message=message, for_types=('Discussion Item',), area_id="comments")


    def createAreaRules(self):
        context = self.context
        catalog = getToolByName(context, 'portal_catalog') 
        results = catalog(object_provides=IRoomArea.__identifier__,
                          path='/'.join(context.getPhysicalPath()))

        for brain in results:
            area = brain.getObject()
        
            subject_created=translate(_('notify_subj_created',
                                        default=u'[${room_title}] New document in area ${area_title}',
                                        mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.getId()}),
                                      context=context.REQUEST)
            message_created=translate(_('notify_msg_created',
                                        default=u'The document "${title}" has been created.\n'
                                                u'\n'
                                                u'${text}\n'
                                                u'\n'
                                                u'You can click on the following link to see it:\n'
                                                u'${url}'),
                                      context=context.REQUEST)
            rule_title = translate(_('notify_title_created',
                                     default=u'[${room_title}] notify for new document inside ${area_title}',
                                     mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.Title()}),
                                     context=context.REQUEST)
            rule_description = translate(_('notify_description_created',
                                           default=u'All users inside the notification group of the area '
                                                   u'${area_title} inside the room ${room_title} will be '
                                                   u'mailed when new contents are added',
                                           mapping={"room_title" : context.Title(), "area_title": area.Title()}),
                                         context=context.REQUEST)
            self.createRule(context, area, rule_id="%s-%s-created" % (context.getId(), area.getId()), rule_title=rule_title,
                            rule_description=rule_description, rule_event=IObjectAddedEvent,
                            subject=subject_created, message=message_created)

            subject_modified=translate(_('notify_subj_modified',
                                         default=u'[${room_title}] document modified inside area ${area_title}',
                                         mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.getId()}),
                                       context=context.REQUEST)
            message_modified=translate(_('notify_msg_modified',
                                         default=u'The document "${title}" has been modified.\n'
                                                 u'You can click on the following link to see it:\n'
                                                 u'${url}'),
                                       context=context.REQUEST)
            rule_title = translate(_('notify_title_modified',
                                     default=u'[${room_title}] notify for document edited inside ${area_title}',
                                     mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.Title()}),
                                     context=context.REQUEST)
            rule_description = translate(_('notify_description_modified',
                                           default=u'All users inside the notification group of the area '
                                                   u'${area_title} inside the room ${room_title} will be '
                                                   u'mailed when contents are modified',
                                           mapping={"room_title" : context.Title(), "area_title": area.Title()}),
                                         context=context.REQUEST)
            self.createRule(context, area, rule_id="%s-%s-modified" % (context.getId(), area.getId()), rule_title=rule_title,
                            rule_description=rule_description,  rule_event=IObjectModifiedEvent,
                            subject=subject_modified, message=message_modified)

            subject_deleted=translate(_('notify_subj_deleted',
                                        default=u'[${room_title}] document deleted inside area ${area_title}',
                                        mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.getId()}),
                                      context=context.REQUEST)
            message_deleted=translate(_('notify_msg_deleted',
                                        default=u'The document "${title}" has been deleted.'),
                                      context=context.REQUEST)
            rule_title = translate(_('notify_title_deleted',
                                     default=u'[${room_title}] notify for document deleted inside ${area_title}',
                                     mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.Title()}),
                                   context=context.REQUEST)
            rule_description = translate(_('notify_description_deleted',
                                           default=u'All users inside the notification group of the area '
                                                   u'${area_title} inside the room ${room_title} will be '
                                                   u'mailed when contents are deleted',
                                           mapping={"room_title" : context.Title().decode('utf-8'), "area_title": area.Title()}),
                                         context=context.REQUEST)
            self.createRule(context, area, rule_id="%s-%s-deleted" % (context.getId(), area.getId()), rule_title=rule_title,
                            rule_description=rule_description, rule_event=IObjectRemovedEvent,
                            subject=subject_deleted, message=message_deleted)

    def createRule(self, context, rule_context, rule_id, rule_title, rule_description,
                   rule_event, message, subject, for_types=None, area_id=None):
        """
        Enabled types are taken from the Plone registry, or you can manually set them using for_types
        Id of the area (used for getting the notification group) is taken from current area, or by area_id param
        """
        registry = queryUtility(IRegistry)
        settings = registry.forInterface(IGroupwareNotifySettings, check=False)
        #create the rule
        rule = Rule()
        rule.__name__ = rule_id
        rule.event = rule_event
        rule.title = rule_title
        rule.description = rule_description
        #add the rule to rule's storage
        storage = getUtility(IRuleStorage)
        # chooser = INameChooser(storage)
        if rule_id not in storage.keys():
            storage[rule_id] = rule
            #set the action and add it to the rule
            action = MailForGroupwareNotificationAction(area_id)
            if settings and settings.default_email_sender:
                action.source = settings.default_email_sender
            action.sender = None
            action.subject = subject
            action.message = message
            rule.actions.append(action)

            if not for_types:
                #set the condition and add it to the rule
                if settings:
                    allowed_types = rule_context.getLocallyAllowedTypes()
                    types_list =  set(allowed_types).difference(settings.black_list)
                    condition = PortalTypeCondition()
                    condition.check_types=tuple(types_list)
                    rule.conditions.append(condition)  
            else:
                # explicit types
                condition=PortalTypeCondition()
                condition.check_types=tuple(for_types)
                rule.conditions.append(condition)
            
            logger.info('Created rule %s' % rule_id)
            
        #assignment
        rule_id=rule.id.replace('++rule++','')
        assignable = IRuleAssignmentManager(rule_context)
        assignable[rule_id] = RuleAssignment(rule_id)
        assignable[rule_id].bubbles=True
        get_assignments(storage[rule_id]).insert('/'.join(rule_context.getPhysicalPath()))
        logger.info('Enabled rule %s on %s' % (rule_id, rule_context.Title()))
