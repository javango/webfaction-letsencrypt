# webfaction-letsencrypt
This script is originally from nik (https://community.webfaction.com/users/7628/nik) posted at https://community.webfaction.com/questions/19988/using-letsencrypt/20510 attempting to automate a couple of steps.

Fully Automated Let's Encrypt integration for WebFaction

Work In Progress for a fully automated solution to get Let's Encrypt setup for Web Faction.

THIS SCRIPT WILL CHANGE YOUR WEBSITES AND COULD RENDER THEM UN-USABLE,  YOU HAVE BEEN WARNED

This scrupt will create a new application that is shared by all websites,  this application will be mounted at /.well-known for each website,  the script will then use acme.sh to update the certificate

# Status

This script is not ready for use,  it is close but has not been tested

# How To

 * Create the website(s) you wish to enable ssl for,  this script expects those sites to exists as https sites.
 * TODO Need to add notes on how to setup the redirect from the http version to the https version.
 * Install acme.sh, from a terminal "curl https://get.acme.sh | sh"
 * Clone this repo, from a terminal "git clone https://github.com/javango/webfaction-letsencrypt.git"
 * Create user_config.py, copy user_config.py.example to user_config.py edit the new file and update your user, password, web and certificate list
 * execute the script 'python2.7 process_certificates.py init' to create the well-known application and add to each website
 * execute the script 'python2.7 process_certificates.py'

# TODO

 * Automate the ssl_redirect app and website (This is partially done)
 * Force application / website names to lower case
