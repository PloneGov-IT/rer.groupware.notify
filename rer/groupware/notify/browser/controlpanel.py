# -*- coding: utf-8 -*-

#from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from Products.statusmessages.interfaces import IStatusMessage

from plone.app.registry.browser import controlpanel

from z3c.form import button
from z3c.form import group
from z3c.form import field

from rer.groupware.notify.interfaces import IGroupwareNotifySettings
from rer.groupware.notify import messageFactory as _


class GroupwareNotifySettingsEditForm(controlpanel.RegistryEditForm):

    schema = IGroupwareNotifySettings
    fields = field.Fields(IGroupwareNotifySettings)
    id = "GroupwareNotifySettingsEditForm"
    label = _(u"Groupware Notify settings")
    description = _(u"help_groupwarenotify_settings_editform",
                    default=u"Manage Groupware notification system")

    @button.buttonAndHandler(_('Save'), name='save')
    def handleSave(self, action):
        data, errors = self.extractData()
        if errors:
            self.status = self.formErrorsMessage
            return
        changes = self.applyChanges(data)
        IStatusMessage(self.request).addStatusMessage(_(u"Changes saved"),
                                                      "info")
        self.context.REQUEST.RESPONSE.redirect("@@groupware-notify-settings")

    @button.buttonAndHandler(_('Cancel'), name='cancel')
    def handleCancel(self, action):
        IStatusMessage(self.request).addStatusMessage(_(u"Edit cancelled"),
                                                      "info")
        self.request.response.redirect("%s/%s" % (self.context.absolute_url(),
                                                  self.control_panel_view))


class GroupwareNotifySettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = GroupwareNotifySettingsEditForm
    #index = ViewPageTemplateFile('controlpanel.pt')
