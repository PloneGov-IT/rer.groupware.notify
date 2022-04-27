# -*- coding: utf-8 -*-

from zope.interface import Interface
from zope import schema

from rer.groupware.notify import messageFactory as _


class IGroupwareNotifyLayer(Interface):
    """Interface rer.groupware.notify for the layer"""


class IGroupwareNotifySettings(Interface):
    """
    Settings used in the control panel for Groupware notifications
    """

    black_list = schema.Tuple(
        title=_("Types blacklist"),
        description=_('help_black_list',
                      default="Content types in this blacklist will not be added to the types of documents notified.\n"
                              "Please note that changes done to this list will only affect new notification groups."),
        required=False,
        default=('Folder', 'Topic', 'Collection', ),
        value_type=schema.Choice(vocabulary="plone.app.vocabularies.ReallyUserFriendlyTypes"),
    )

    default_email_sender = schema.TextLine(
        title=_("Defaul email sender"),
        description=_('help_default_emai_sender',
                      default="Insert a default email sender for notifications"),
        required=False,
    )
