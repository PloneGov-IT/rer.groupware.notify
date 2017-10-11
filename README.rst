Manage notification for **Groupware**, automatically creating notification groups and rules

Quick guide
===========

This is a notification package for RER Groupware.

Adding this to your buildout will automatically create new groups when a Room is created.
A new group for every Room's Area is created. Member inside those groupw will get **notified by mail** every time
that a new document is *created*, *modified* or *deleted*.

Installing this product will also register a **new portlet**. This portlet will only appear inside a Room, and
members if the Room will be able to manage subscriptions by themself.

You can set a default sender email that will be used to create new rules. You can set it from @@groupware-notify-settings control panel

Compatibility
=============

This product is compatible with Plone 5.

For Plone 4, use version < 2.* and `plone4` branch.
