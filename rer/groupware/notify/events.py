# -*- coding: utf-8 -*-

from zope.i18n import translate

from zope.component import getUtility
from zope.app.container.interfaces import IObjectAddedEvent, IObjectRemovedEvent
from zope.app.container.interfaces import INameChooser

from Products.CMFCore.utils import getToolByName
#from Products.Archetypes.interfaces import IObjectEditedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from plone.contentrules.engine.assignments import RuleAssignment
from plone.contentrules.engine.interfaces import IRuleAssignmentManager
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.app.contentrules.rule import Rule, get_assignments

from rer.groupware.room.interfaces import IRoomArea
from rer.groupware.notify import logger
from rer.groupware.notify import messageFactory as _

from rer.groupware.notify.action.mail import MailForGroupwareNotificationAction


class CreateNotificationGroupsEvent:
    """Create notification groups:
    
    For every Area inside this Room we will create a notification group
    """
    
    def __init__(self, context, event):
        groups_tool = getToolByName(context,'portal_groups')
        catalog = getToolByName(context, 'portal_catalog')
        room_id = context.getId()
        room_title = context.Title()
        sgm_groups=[]

        results = catalog(object_provides=IRoomArea.__identifier__)

        for area in results:
            group_id = '%s.%s.notify' % (room_id, area.getId)
            groups_tool.addGroup(id=group_id,
                                 title=translate(_(u"${room_title} ${area_title} notifications",
                                                   mapping={"room_title" : room_title,
                                                            "area_title" : area.Title,}),
                                                   context=context.REQUEST))
            logger.info('Created group %s' % group_id)
            sgm_groups.append('%s.%s.notify' % (room_id, area.getId))
        #sgm_groups.append('%s.hosts' %room_id)
        self.addSGMEntries(context, sgm_groups, '%s.coordinators' % room_id)
        
    def addSGMEntries(self, context, managed_groups, coordinator):
        """
        Set SGM properties with new-created groups.
        """
        portal_properties = getToolByName(context, 'portal_properties', None)
        if not portal_properties:
            return
        sgm_properties = getattr(portal_properties, 'simple_groups_management_properties', None)
        if not sgm_properties:
            logger.warning('SimpleGroupsManagement not found. Skipping configuration.')
            return
        sgm_groups = set(sgm_properties.getProperty('sgm_data', None))
        for group in managed_groups:
            sgm_groups.add('%s|%s' % (coordinator, group))
        
        sgm_properties._updateProperty('sgm_data',tuple(sgm_groups))
        logger.info('SGM properties set.')


class CreateNotificationRulesEvent:
    """
    Create 3 content rules (add, edit, and delete) with the new Groupware action.
    Enable the rule on the room
    """ 
    
    def __init__(self, context, event):
        room_title = context.Title()
        catalog = getToolByName(context, 'portal_catalog')
        
        results = catalog(object_provides=IRoomArea.__identifier__)

        for area in results:
        
            subject_created=translate(_('notify_subj_created',
                                        default=u'[${room_title}] New document in area ${area_title}',
                                        mapping={"room_title" : context.Title(), "area_title": area.getId}),
                                       context=context.REQUEST)
            message_created=translate(_('notify_msg_created',
                                        default=u'The document "${title}" has been created.\n'
                                                u'You can click on the following link to see it:\n'
                                                u'${url}'),
                                      context=context.REQUEST)
            rule_title = translate(_('notify_title_created',
                                     default=u'[${room_title}] notify for new document inside ${area_title}',
                                     mapping={"room_title" : context.Title(), "area_title": area.Title}),
                                   context=context.REQUEST)
            rule_description = translate(_('notify_description_created',
                                           default=u'All users inside the notification group of the area '
                                                   u'${area_title} inside the room ${room_title} will be '
                                                   u'mailed when new contents are added',
                                           mapping={"room_title" : context.Title(), "area_title": area.Title}),
                                         context=context.REQUEST)
            self.createRule(context, area, rule_id="%s-%s-created" % (context.getId(), area.getId), rule_title=rule_title,
                            rule_description=rule_description, rule_event=IObjectAddedEvent,
                            subject=subject_created, message=message_created)

            subject_modified=translate(_('notify_subj_modified',
                                         default=u'[${room_title}] document modified inside area ${area_title}',
                                         mapping={"room_title" : context.Title(), "area_title": area.getId}),
                                       context=context.REQUEST)
            subject_modified=translate(_('notify_msg_modified',
                                         default=u'The document "${title}" has been modified.\n'
                                                 u'You can click on the following link to see it:\n'
                                                 u'${url}'),
                                       context=context.REQUEST)
            rule_title = translate(_('notify_title_modified',
                                     default=u'[${room_title}] notify for document edited inside ${area_title}',
                                     mapping={"room_title" : context.Title(), "area_title": area.Title}),
                                   context=context.REQUEST)
            rule_description = translate(_('notify_description_modified',
                                           default=u'All users inside the notification group of the area '
                                                   u'${area_title} inside the room ${room_title} will be '
                                                   u'mailed when contents are modified',
                                           mapping={"room_title" : context.Title(), "area_title": area.Title}),
                                         context=context.REQUEST)
            self.createRule(context, area, rule_id="%s-%s-modified" % (context.getId(), area.getId), rule_title=rule_title,
                            rule_description=rule_description,  rule_event=IObjectModifiedEvent,
                            subject=subject_modified, message=subject_modified)

            subject_deleted=translate(_('notify_subj_deleted',
                                        default=u'[${room_title}] document deleted inside area ${area_title}',
                                        mapping={"room_title" : context.Title(), "area_title": area.getId}),
                                       context=context.REQUEST)
            message_deleted=translate(_('notify_msg_deleted',
                                        default=u'The document "${title}" has been deleted.'),
                                      context=context.REQUEST)
            rule_title = translate(_('notify_title_deleted',
                                     default=u'[${room_title}] notify for document deleted inside ${area_title}',
                                     mapping={"room_title" : context.Title(), "area_title": area.Title}),
                                   context=context.REQUEST)
            rule_description = translate(_('notify_description_deleted',
                                           default=u'All users inside the notification group of the area '
                                                   u'${area_title} inside the room ${room_title} will be '
                                                   u'mailed when contents are deleted',
                                           mapping={"room_title" : context.Title(), "area_title": area.Title}),
                                         context=context.REQUEST)
            self.createRule(context, area, rule_id="%s-%s-deleted" % (context.getId(), area.getId), rule_title=rule_title,
                            rule_description=rule_description, rule_event=IObjectRemovedEvent,
                            subject=subject_deleted, message=message_deleted)

    def createRule(self, context, area, rule_id, rule_title, rule_description, rule_event, message, subject):
        #create the rule
        rule = Rule()
        rule.__name__ = rule_id
        rule.event = rule_event
        rule.title = rule_title
        rule.description = rule_description
        #add the rule to rule's storage
        storage = getUtility(IRuleStorage)
        chooser = INameChooser(storage)
        storage[rule_id] = rule
        #set the action and add it to the rule
        action = MailForGroupwareNotificationAction()
        
        action.sender = None
        action.subject=subject
        action.message=message
        rule.actions.append(action)
        #assignment
        rule_id=rule.id.replace('++rule++','')
        assignable = IRuleAssignmentManager(area.getObject())
        assignable[rule_id] = RuleAssignment(rule_id)
        assignable[rule_id].bubbles=True
        get_assignments(storage[rule_id]).insert(area.getPath())
        logger.info('Created rule %s, enabled on %s' % (rule_id, area.Title))
