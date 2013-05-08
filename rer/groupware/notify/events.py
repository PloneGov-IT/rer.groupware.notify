# -*- coding: utf-8 -*-

from Products.CMFCore.utils import getToolByName

class CreateNotificationGroupsEvent:
    """Create notification groups:
    
    """
    
    def __init__(self, context, event):
        context = self.context
        groups_tool = getToolByName(context,'portal_groups')
        room_id = context.getId()
        room_title = context.Title()
        sgm_groups=[]

        groups_tool.addGroup(id='%s.members' %room_id,
                             title=translate(_(u"${room_title} members",
                                               mapping={u"room_title" :room_title,}),
                                             context=self.context.REQUEST))
        sgm_groups.append('%s.members' %room_id)
        groups_tool.addGroup(id='%s.membersAdv' %room_id,
                             title=translate(_(u"${room_title} membersAdv",
                                               mapping={u"room_title" :room_title,}),
                                             context=self.context.REQUEST))
        sgm_groups.append('%s.membersAdv' %room_id)
        groups_tool.addGroup(id='%s.notifyDocs' %room_id,
                             title=translate(_(u"${room_title} notifyDocs",
                                               mapping={u"room_title" :room_title,}),
                                             context=self.context.REQUEST))
        groups_tool.addGroup(id='%s.notifyNewsEvents' %room_id,
                             title=translate(_(u"${room_title} notifyNewsEvents",
                                               mapping={u"room_title" :room_title,}),
                                             context=self.context.REQUEST))
        groups_tool.addGroup(id='%s.coordinators' %room_id,
                             title=translate(_(u"${room_title} coordinators",
                                               mapping={u"room_title" :room_title,}),
                                             context=self.context.REQUEST))
        groups_tool.addGroup(id='%s.hosts'%room_id,
                             title=translate(_(u"${room_title} hosts",
                                               mapping={u"room_title" :room_title,}),
                                             context=self.context.REQUEST))
        sgm_groups.append('%s.hosts' %room_id)
        
        self.addSGMEntries(sgm_groups,'%s.coordinators' %room_id)
        
    def addSGMEntries(self,managed_groups,coordinator):
        """
        Set SGM properties with new-created groups.
        """
        portal_properties = getToolByName(self.context, 'portal_properties', None)
        if not portal_properties:
            return
        sgm_properties = getattr(portal_properties, 'simple_groups_management_properties', None)
        if not sgm_properties:
            return
        sgm_groups = set(sgm_properties.getProperty('sgm_data', None))
        for group in managed_groups:
            sgm_groups.add('%s|%s' %(coordinator,group))
        
        sgm_properties._updateProperty('sgm_data',tuple(sgm_groups))
        logger.info('SGM properties set.')


class CreateNotificationRulesEvent:
    
    def __init__(self, context, event):
        print "b"
