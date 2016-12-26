#!/usr/bin/python2

import os

import sys

import subprocess

import xmlrpclib

from user_config import *

HOME_PATH='/home/{user}/'.format(user=USER)
ACME_PATH='/home/{user}/.acme.sh'.format(user=USER)

def create_letsencrypt_certificate(cert_name, cert_domain, other_domains):
    """ Creates the let's encrypt certificate,  this is run once per certificate """
    if DEBUG > 0:
        print 'Need to create initial certificate for {}'.format(cert_name)

    domains = '-d {}'.format(cert_domain)
    for domain in other_domains:
        domains += ' -d {}'.format(domain)

    test = '' # ' --test'

    command = '{acme_path}/acme.sh --issue{test} {domains} -w {home}letsencrypt/'.format(home=HOME_PATH, acme_path=ACME_PATH, test=test, domains=domains)
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
            server.create_certificate(ses, cert_name, domain_certif, pv_key, intermediate_cert)


if __name__ == '__main__':
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
