# -*- coding: utf-8 -*-

from zope.i18n import translate

from Products.CMFCore.utils import getToolByName

from rer.groupware.room.interfaces import IRoomArea
from rer.groupware.notify import logger
from rer.groupware.notify import messageFactory as _


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
            groups_tool.addGroup(id='%s.%s.notify' % (room_id, area.getId),
                                 title=translate(_(u"${room_title} ${area_title} notifications",
                                                   mapping={"room_title" : room_title,
                                                            "area_title" : area.Title,}),
                                                   context=context.REQUEST))
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
        
        results = catalog(object_provides=IRoomArea.__identifier__)

        for area in results:
        
            subject_created=translate(_('notify_subj_created',
                                        default=u'[${room_title}] New document in area ${area_title}',
                                        mapping={"room_title" : context.Title(), "area_title": area.getId}),
                                       context=context.REQUEST)
            message_created=translate(_('notify_msg_created',
                                        default=u'A document "${title}" has been created.\n'
                                                u'You can click on the following link to see it:\n'
                                                u'${url}'),
                                      context=context.REQUEST)
            self.createRule(context, rule_title="%s-%s-created" % (context.getId(), area.getId),
                            rule_event=IObjectAddedEvent,
                            subject=subject_created,
                            message=message_created)

            subject_modified=translate(_('notify_subj_modified',
                                         default=u'[${room_title}] document modified inside area ${area_title}',
                                         mapping={"room_title" : context.Title(), "area_title": area.getId}),
                                       context=context.REQUEST)
            subject_modified=translate(_('notify_msg_modified',
                                         default=u'The document "${title}" has been modified.\n'
                                                 u'You can click on the following link to see it:\n'
                                                 u'${url}'),
                                       context=context.REQUEST)
            self.createRule(context, rule_title="%s-%s-modified" % (context.getId(), area.getId),
                            rule_event=IObjectXXX,
                            subject=subject_modified,
                            message=subject_modified)

            subject_deleted=translate(_('notify_subj_deleted',
                                        default=u'[${room_title}] document deleted inside area ${area_title}',
                                        mapping={"room_title" : context.Title(), "area_title": area.getId}),
                                       context=context.REQUEST)
            message_deleted=translate(_('notify_msg_modified',
                                        default=u'The document "${title}" has been deleted.\n'),
                                      context=context.REQUEST)
            self.createRule(context, rule_title="%s-%s-deleted" % (context.getId(), area.getId),
                            rule_event=IObjectRemovedEvent,
                            message="%s\n\n%s" %(no_reply_txt,message_deleted),
                            subject=subject_deleted,
                            message=message_deleted)

    def createRule(self, context, rule_title, rule_event, message, subject):
        #create the rule
        rule=Rule()
        rule.event=rule_event
        rule.title=rule_title
        #add the rule to rule's storage
        storage = getUtility(IRuleStorage)
        chooser = INameChooser(storage)
        storage[chooser.chooseName(None, rule)] = rule
        #set the condition and add it to the rule
        condition=PortalTypeCondition()
        condition.check_types=types_list
        rule.conditions.append(condition)  
        #set the action and add it to the rule
        action=MailGroupAction()
        
        action.members = []
        action.source = None
        action.groups=[group]
        action.subject=subject
        action.message=message
        rule.actions.append(action)
        #assignment
        rule_id=rule.id.replace('++rule++','')
        assignable = IRuleAssignmentManager(self.context)
        assignable[rule_id] = RuleAssignment(rule_id)
        assignable[rule_id].bubbles=True
        get_assignments(storage[rule_id]).insert('/'.join(self.context.getPhysicalPath()))
