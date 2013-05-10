#!/bin/sh

DOMAIN='rer.groupware.notify'

i18ndude rebuild-pot --pot ${DOMAIN}.pot --create ${DOMAIN} --merge ${DOMAIN}-manual.pot ..
i18ndude sync --pot ${DOMAIN}.pot ./*/LC_MESSAGES/${DOMAIN}.po

# Compile po files
for lang in $(find . -mindepth 1 -maxdepth 1 -type d); do
    if test -d $lang/LC_MESSAGES; then
        msgfmt -o $lang/LC_MESSAGES/${DOMAIN}.mo $lang/LC_MESSAGES/${DOMAIN}.po
    fi
done