Changelog
=========

2.0.2 (unreleased)
------------------

- Nothing changed yet.


2.0.1 (2017-10-24)
------------------

- Fix send email module to read email infos from registry.
  [cekk]


2.0.0 (2017-10-11)
------------------

- Add uninstall profile
  [cekk]
- Plone 5 compatibility
  [cekk]

1.3.3 (2015-09-24)
------------------

- Add plone.api [cekk]


1.3.2 (2015-09-22)
------------------

- Refactored `listNotificationGroups` method in the portlet to speedup,
  and add ramcache
  [cekk]


1.3.1 (2013-11-29)
------------------

- Fixed redirect after subscription for files and images [cekk]


1.3.0 (2013-11-05)
------------------

- Fixed translation [cekk]
- Added multi-language support in creation event [cekk]
- Added for_types exception for PloneBoard area. Now rules are filtered for PloneboardComment [cekk]
- Add fullname in portal_message after subscription/unsubscription action [cekk]
- Add check to show areas: if is excluded from nav, doesn't show it in the portlet [cekk]

1.2.2 (2013-10-21)
------------------

- Fixed query catalog for areas in room in the event. Now results are filtered by room path [cekk]
- Fix portlet's available method [cekk]

1.2.1 (2013-09-24)
------------------

- Fix rule mail sendere for rooms with accents [cekk]
- Fix rule message for modified contents [cekk]

1.2.0 (2013-08-02)
------------------

- Use plone.stringinterp for standard Plone interpolations
  [keul]

1.1.0 (2013-07-26)
------------------

- If default_email_sender registry property is set, the sender of rules
  will be set with that address
  [cekk]

1.0.0 (2013-06-24)
------------------

- Initial release
