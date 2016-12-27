#!/usr/bin/python2

import os

import sys

import subprocess

import xmlrpclib

DEBUG=0
LETSENCRYPT_APP_NAME = 'letsencrypt'
APP_PATH = os.path.dirname(os.path.abspath(__file__))

from user_config import *

# ----------------------------------------------------------------------- letsencrypt application
def check_letsencrypt_application():
    """ Returns true if the letsencrypt application exists """
    if DEBUG > 0:
        print "Checking letsencrypt app '{app_name}'".format(app_name=LETSENCRYPT_APP_NAME)

    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    ses, acc = server.login(USER, PASS, WEB, 2)

    app_list = server.list_apps(ses)

    for app in app_list:
        if app['name'] == LETSENCRYPT_APP_NAME:
            if DEBUG > 0:
                print "Application Exists"
            return True

    if DEBUG > 0:
        print "Application Does Not Exist"

    return False


def create_letsencrypt_application():
    """ If the lets encrypt application does not exist create it """
    # connect to Webfaction API
    if DEBUG > 0:
        print "Creating Let's Encrypt Application '{app_name}'".format(app_name=LETSENCRYPT_APP_NAME)
        
    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    ses, acc = server.login(USER, PASS, WEB, 2)

    well_known_path = '{app_path}/.well-known'.format(app_path=APP_PATH)
    server.create_app(ses, LETSENCRYPT_APP_NAME, 'symlink_static_only', False, well_known_path, False)

    if DEBUG > 0:
        print "Application Created"

    return True

# ----------------------------------------------------------------------- wellknown url
def check_wellknown(site_name):
    """ Returns a tuple of true/false and the site definition from the webfaction aip
        True if wellknown url exists for the give site False otherwise,
        Will sys.exit if the site does not exist
    """
    if DEBUG > 0:
        print 'checking wellknown {}'.format(site_name)

    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    ses, acc = server.login(USER, PASS, WEB, 2)

    site_list = server.list_websites(ses)

    for site in site_list:
        if DEBUG > 3:
            print 'checking site {site} for match to {site_name}'.format(site=site['name'], site_name=site_name)

        if site['name'] == site_name:
            for app, url in site['website_apps']:
                if DEBUG > 3:
                    print "checking site {app} for {letsencrypt}".format(app=app, letsencrypt=LETSENCRYPT_APP_NAME)
                if app == LETSENCRYPT_APP_NAME:
                    if DEBUG > 0:
                        print "Wellknown Exists"
                    return True, site

            if DEBUG > 0:
                print "Wellknown Does Not Exist"
            return False, site

    sys.exit("Website {0} Does Not Exist".format(site_name))
    

def create_wellknown(site_name, site_definition):
    """ If the lets encrypt application does not exist create it """
    website_apps = site_definition['website_apps']
    website_apps.append([LETSENCRYPT_APP_NAME, '/.well-known'])

    # connect to Webfaction API
    if DEBUG > 1:
        print "Adding letsencryt url"

    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    ses, acc = server.login(USER, PASS, WEB, 2)

    server.update_website(ses, \
          site_definition['name'], \
          site_definition['ip'], \
          site_definition['https'], \
          site_definition['subdomains'], \
          site_definition['certificate'], \
          *website_apps)

    if DEBUG > 1:
        print "Url Created"

    return True

 
def add_certificate_to_website(site_name, site_def):
    """ Make sure the site is https and the certificate is enabled """

    # connect to Webfaction API
    if DEBUG > 1:
        print "Adding certificate to website"

    server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
    ses, acc = server.login(USER, PASS, WEB, 2)

    server.update_website(ses, \
          site_definition['name'], \
          site_definition['ip'], \
          True, \
          site_definition['subdomains'], \
          site_name, \
          *site_definition['website_apps'])

    if DEBUG > 1:
        print "certificate added"

    return True


# ----------------------------------------------------------------------- letsencrypt certificate
def create_letsencrypt_certificate(cert_name, cert_domain, other_domains):
    """ Creates the let's encrypt certificate,  this is run once per certificate """
    if DEBUG > 0:
        print 'Need to create initial certificate for {}'.format(cert_name)

    domains = '-d {}'.format(cert_domain)
    for domain in other_domains:
        domains += ' -d {}'.format(domain)

    test = '' # ' --test'

    command = '{acme_path}/acme.sh --issue{test} {domains} -w {app_path}'.format(app_path=APP_PATH, acme_path=ACME_PATH, test=test, domains=domains)
    proc = subprocess.Popen(command.split(' '), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if DEBUG > 2:
        print out
        print err
    if 'Cert success.' in out:
        if DEBUG > 0:
            print 'Create Certificate success.'
    else:
        print 'Failed to create certificate for {}'.format(cert_name)


def update_webfaction_certificate(cert_name, cert_domain, other_domains):
        """ Updates a single certificate """
        if DEBUG > 0:
            print "Processing {cert_name} in {cert_domain}".format(cert_name=cert_name, cert_domain=cert_domain)

        parent_cert_dir = '/home/{0}/.acme.sh'.format(USER) # WHAT IS THIS USED FOR??

        os.chdir('{home}.acme.sh/{cert_comain}'.format(home=HOME_PATH, cert_comain=cert_domain))

        # Test if current working directory is the valid one
        try:
            assert os.getcwd() != parent_cert_dir
        except AssertionError as e:
            sys.exit('Current working directory is not {}! Instead is {}. Exception: {}'.format(parent_cert_dir, os.getcwd(), e))

        # connect to Webfaction API
        server = xmlrpclib.ServerProxy('https://api.webfaction.com/')
        ses, acc = server.login(USER, PASS, WEB, 2)

        # read domain certificate and store it as a variable
        try:
            file_to_read = '{}.cer'.format(cert_domain)
            assert file_to_read in os.listdir('.')
            with open(file_to_read, 'r') as f:
                domain_certif = f.read()
        except AssertionError as e:
            sys.exit('The file \"{}\" does not exist inside \"{}\". Exception: {}'.format(file_to_read, os.getcwd(), e))
        except IOError as e:
            sys.exit('Problem with opening file \"{}\". Exception: {}'.format(file_to_read, os.getcwd(), e))
        finally:
            f.close()

       # read private key certificate and store it as a variable
        try:
            file_to_read = '{}.key'.format(cert_domain)
            assert file_to_read in os.listdir('.')
            with open(file_to_read, 'r') as f:
                pv_key = f.read()
        except AssertionError as e:
            sys.exit('The file \"{}\" does not exist inside \"{}\". Exception: {}'.format(file_to_read, os.getcwd(), e))
        except IOError as e:
            sys.exit('Problem with opening file \"{}\". Exception: {}'.format(file_to_read, os.getcwd(), e))
        finally:
            f.close()

       # read intermediate certificate and store it as a variable
        try:
            file_to_read = 'ca.cer'
            assert file_to_read in os.listdir('.')
            with open(file_to_read, 'r') as f:
                intermediate_cert = f.read()
        except AssertionError as e:
            sys.exit('The file \"{}\" does not exist inside \"{}\". Exception: {}'.format(file_to_read, os.getcwd(), e))
        except IOError as e:
            sys.exit('Problem with opening file \"{}\". Exception: {}'.format(file_to_read, os.getcwd(), e))
        finally:
            f.close()

        # Update the renewed certificate
        try:
            server.update_certificate(ses, cert_name, domain_certif, pv_key, intermediate_cert)
        except:
            # certificate does not exist,  try to create
            server.create_certificate(ses, cert_name, domain_certif, pv_key, intermediate_cert)
            # re-use check well-known to get the site definition
            exists, site = check_wellknown(cert_name)
            add_certificate_to_website(cert_name, site)


def setup_webfaction():
    
    if not check_letsencrypt_application():
        if not create_letsencrypt_application():
            sys.exit("Not able to create Let's Encrypt Application via WebFaction API")

    for cert_name, cert_domain, other_domains in CERTS:
        exists, site = check_wellknown(cert_name)
        if not exists:
            if not create_wellknown(cert_name, site):
                sys.exit("Not able to create wellknown via WebFaction API '{}'".format(cert_name))


if __name__ == '__main__':
    # verify the webfaction assets exist
    setup_webfaction()

    # Run the command advised by acme.sh script in order to renew the certificates (each certificate lasts 90 days, thus
    # it is permitted by LetsEncrypt to renew certificates every 60 days - 30 days before expiration)
    # So this script will run as a cron job in order for the certs to be renewed.
    os.chdir('/home/{0}'.format(USER))

    update_webfaction = False # Set this to True if we need to update certifictes in webfaction

    # First see if the certificate director exists,  if not call acme to create the initial certificate
    for cert_name, cert_domain, other_domains in CERTS:
        domain_path = '.acme.sh/{}'.format(cert_domain)
        if not os.path.isdir(domain_path): # TODO This is not right,  when acme fails it leaves the directory.  
            create_letsencrypt_certificate(cert_name, cert_domain, other_domains)
            update_webfaction = True
        elif DEBUG > 2:
            print 'Certificate dir for {} already exists'.format(cert_name)


    # Call acme.sh to see if any certificates need to be updated
    proc = subprocess.Popen(['.acme.sh/acme.sh', 'cron'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()

    if DEBUG > 2:
        print out

    if err:
        sys.exit("An error occurred during the renewal process. Error: {}".format(err))
    elif DEBUG > 0:
        print 'successfully ran acme.sh cron'

    update_webfaction = update_webfaction or 'Cert success.' in out

    if update_webfaction:
        if DEBUG > 0:
            print 'Need to update webfaction'

        for cert_name, cert_domain, other_domains in CERTS:
            update_webfaction_certificate(cert_name, cert_domain, other_domains)

    else:
        if DEBUG > 0:
            print 'did NOT need to update webfaction'

