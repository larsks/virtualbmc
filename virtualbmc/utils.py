#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import os
import libvirt

import exception

CONFIG_PATH = os.path.join(os.path.expanduser('~'), '.vbmc')


class libvirt_open(object):

    def __init__(self, uri, sasl_username=None, sasl_password=None,
                 readonly=False):
        self.uri = uri
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.readonly = readonly

    def __enter__(self):
        try:
            if self.sasl_username and self.sasl_password:

                def request_cred(credentials, user_data):
                    for credential in credentials:
                        if credential[0] == libvirt.VIR_CRED_AUTHNAME:
                            credential[4] = self.sasl_username
                        elif credential[0] == libvirt.VIR_CRED_PASSPHRASE:
                            credential[4] = self.sasl_password
                    return 0

                auth = [[libvirt.VIR_CRED_AUTHNAME,
                         libvirt.VIR_CRED_PASSPHRASE], request_cred, None]
                flags = libvirt.VIR_CONNECT_RO if self.readonly else 0
                self.conn = libvirt.openAuth(self.uri, auth, flags)
            elif self.readonly:
                self.conn = libvirt.openReadOnly(self.uri)
            else:
                self.conn = libvirt.open(self.uri)

            return self.conn

        except libvirt.libvirtError as e:
            raise exception.LibvirtConnectionOpenError(uri=self.uri, error=e)

    def __exit__(self, type, value, traceback):
        self.conn.close()


def get_libvirt_domain(conn, domain):
    try:
        return conn.lookupByName(domain)
    except libvirt.libvirtError:
        raise exception.DomainNotFound(domain=domain)


def check_libvirt_connection_and_domain(uri, domain, sasl_username=None,
                                        sasl_password=None):
    with libvirt_open(uri, readonly=True, sasl_username=sasl_username,
                      sasl_password=sasl_password) as conn:
        get_libvirt_domain(conn, domain)


def is_pid_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def str2bool(string):
    lower = string.lower()
    if lower not in ('true', 'false'):
        raise ValueError('Value "%s" can not be interpreted as '
                         'boolean' % string)
    return lower == 'true'


def mask_dict_password(dictionary, secret='***'):
    """Replace passwords with a secret in a dictionary."""
    d = dictionary.copy()
    for k in d:
        if 'password' in k:
            d[k] = secret
    return d
