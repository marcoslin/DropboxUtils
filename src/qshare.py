#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import json
import argparse

import dropbox


class Config(object):
    '''
    Simple config object that allow saving
    '''

    DEFAULT_CONFIG = {
        "ACCESS_TOKEN": None,
        "APP_KEY": 'k2jhj5dlji7qyyn',
        "APP_SECRET": 'ca5g8fur6utxrck'
    }

    @classmethod
    def __get_config_file(cls):
        '''Get Config File Path'''
        config_dir = os.path.join(os.environ["HOME"], ".dboxup")
        if not os.path.exists(config_dir):
            os.mkdir(config_dir, 0777)
        return os.path.join(config_dir, "config.json")

    def __init__(self):
        '''Initialize the config object'''
        self._config_dir = self.__get_config_file()
        if os.path.exists(self._config_dir):
            with open(self._config_dir, "r") as fh:
                config = json.load(fh)
        else:
            config = self.DEFAULT_CONFIG
        for key in config:
            if not key.startswith("_"):
                self.__apply_config(key, config[key])

    def __apply_config(self, key, value):
        self.__dict__.update({key: value})

    def save(self):
        # Write config
        config = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                upper_key = key.upper()
                if key != upper_key:
                    raise ValueError("Config key '%s' must be in upper case." % key)
                config[upper_key] = value
        with open(self._config_dir, "w") as fh:
            json.dump(config, fh)


class Dropbox(object):
    '''
    Simple wrapper object to connect to Dropbox
    '''
    def __init__(self):
        '''
        Obtain access_token and get a dropbox client
        '''
        self.config = Config()
        if self.config.ACCESS_TOKEN:
            self.token = self.config.ACCESS_TOKEN
        else:
            self.token = self._authenticate()
        self.client = dropbox.client.DropboxClient(self.token)

    def _authenticate(self):
        flow = dropbox.client.DropboxOAuth2FlowNoRedirect(self.config.APP_KEY, self.config.APP_SECRET)
        authorize_url = flow.start()
        print("- Obtain auth from: %s" % authorize_url)
        code = raw_input("Enter authorization code: ").rstrip()
        access_token, user_id = flow.finish(code)

        self.config.ACCESS_TOKEN = access_token
        self.config.USER_ID = user_id
        self.config.save()

        return access_token

    def client(self):
        return self.client

    def upload(self, filename):
        print("- Uploading %s..." % filename)
        basename = os.path.basename(filename)
        with open(filename, "r") as fh:
            resp = self.client.put_file(basename, fh)
        print("Uploaded '%s'" % resp.get("path"))

    def download(self, filename):
        print("- Downloading %s..." % filename)
        f, metadata = self.client.get_file_and_metadata(filename)
        outfile = os.path.basename(metadata.get("path"))
        if os.path.exists(outfile):
            raise RuntimeError("file %s already exists." % outfile)
        with open(outfile, "wb") as fh:
            fh.write(f.read())
        print("Downloaded '%s'" % outfile)


class App(object):
    @classmethod
    def _handle_error(cls, message=None, exception=None):
        if message:
            if exception:
                print("%s: %s" % (message, exception), file=sys.stderr)
            else:
                print("ERROR: %s" % message, file=sys.stderr)
        elif exception:
            print("ERROR: %s" % exception, file=sys.stderr)
        sys.exit(1)

    def __init__(self):
        p = argparse.ArgumentParser(description='Dropbox File Uploader')
        p.add_argument('action', choices=['get', 'put'])
        p.add_argument('infile', help="name of the file")
        args = p.parse_args()

        if args.action == 'put':
            if not os.path.isfile(args.infile):
                self._handle_error("%s does not exists or not a file." % args.infile)

        self.action = args.action
        self.infile = args.infile

    def run(self):
        # Connect to dropbox
        try:
            dbox = Dropbox()
        except Exception as e:
            self._handle_error("Failed to connect to dropbox", exception=e)

        if self.action == 'get':
            try:
                dbox.download(self.infile)
            except Exception as e:
                self._handle_error("Failed during download", exception=e)
        elif self.action == 'put':
            try:
                dbox.upload(self.infile)
            except Exception as e:
                self._handle_error("Failed during upload", exception=e)


# START
if __name__ == "__main__":
    app = App()
    app.run()
