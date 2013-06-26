#!/bin/bash

MODULE_CONFIG=/etc/httpd/conf.modules.d/00-base.conf
USERDIR_CONF=/etc/httpd/conf.d/userdir.conf
SAMPLE_PHPMYADMIN=/usr/share/phpMyAdmin/config.sample.inc.php
NEW_PHPMYADMIN=/usr/share/phpMyAdmin/config.inc.php
PHP=/usr/bin/php

# CORRECT POLICT

echo "Checking SELinux..."
SELINUX=`getenforce`
echo "SELinux is: $SELINUX"
#BEGIN-D-BUS
# httpd activation
echo "Activation httpd.service"
systemctl enable httpd.service

# mysql activation
echo "Actiovation mysqld.service"
systemctl enable mysqld.service
systemctl restart mysqld.service

#END D-BUS
echo "Modify $NEW_PHPMYADMIN"
if [ -f $NEW_PHPMYADMIN ]; then
    echo "Already modified"
else
    cp $SAMPLE_PHPMYADMIN $NEW_PHPMYADMIN
    if [ $? -ne 0 ]; then
        echo "Problem with setting PHP MyAdmin"
        exit 1
    fi
    sed -i "s|['auth_type'].*|['auth_type'] = 'http'|" $NEW_PHPMYADMIN
fi

echo "Disable unique_id module"
grep "#LoadModule unique_id_module" $MODULE_CONFIG
if [ $? -eq 0 ]; then
    echo "unique_id_module was already disabled"
else
    sed -i "s|LoadModule unique_id_module|#LoadModule unique_id_module|" $MODULE_CONFIG
    echo "unique_id_module was disabled"
fi

echo "Creating configuration file for apache web server"
if [ ! -f "/etc/httpd/$1" ]; then
    if [ ! -f "/etc/httpd/conf.d/$1.conf" ]; then
        rm -f /tmp/$1.conf
        echo "RewriteEngine on" > /tmp/$1.conf
        echo "RewriteRule ^$1 $2/public_html/$1" >> /tmp/$1.conf
        echo "Alias /$1 $2/public_html/$1" >> /tmp/$1.conf
        echo "<Directory \"$2/public_html/$1\" >" >> /tmp/$1.conf
        echo "  Require all granted" >> /tmp/$1.conf
        echo "</Directory>" >> /tmp/$1.conf
        mv /tmp/$1.conf /etc/httpd/conf.d/$1.conf
        echo "Configuration file was successfuly created"
    fi
else
    echo "Configuration file was already created"
fi

if [ -f $USERDIR_CONF ]; then
    echo "Check whether UserDir is enabled"
    grep "UserDir disabled" $USERDIR_CONF
    if [ $? -eq 0 ]; then
        echo "Userdir will be enabled"
        sed -i "s|UserDir disabled||" $USERDIR_CONF
    fi
    grep "#UserDir public_html" $USERDIR_CONF
    if [ $? -eq 0 ]; then
        echo "Userdir public_html is enabled"
        sed -i "s|#UserDir public_html|UserDir public_html|" $USERDIR_CONF
    fi
fi



echo "Restarting httpd.service"
systemctl restart httpd.service
if [ $? -ne 0 ]; then
    echo "Check messages by journalctl -xn"
fi
echo "Restarting httpd.service done"


