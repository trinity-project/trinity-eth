#!/usr/bin/env python
import argparse
import json
import pprint
import traceback

import os
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
from lightwallet.Utils import get_arg
from lightwallet.Settings import settings
from lightwallet.wallet import Wallet

from lightwallet.UserPreferences import preferences

FILENAME_PROMPT_HISTORY = os.path.join(settings.DIR_CURRENT, '.prompt.py.history')

class PromptInterface(object):
    commands = [
                'help',
                'quit',
                'create wallet {path}',
                'open wallet {path}',
                'close',
                'wallet',
                'send {asset} {address} {amount}',
                'export wif {address}',
                'export nep2 {address}',
                'tx {txid}',
                ]
    go_on = True
    Wallet=None
    history = FileHistory(FILENAME_PROMPT_HISTORY)

    def __init__(self):
        self.token_style = style_from_dict({
            Token.Command: preferences.token_style['Command'],
            Token.Neo: preferences.token_style['Neo'],
            Token.Default: preferences.token_style['Default'],
            Token.Number: preferences.token_style['Number'],
        })

    def get_bottom_toolbar(self, cli=None):
        out = []
        try:
            out = [
                (Token.Command, '[%s]' % settings.NET_NAME),

            ]
        except Exception as e:
            pass

        return out

    def quit(self):
        self.go_on = False

    def help(self):
        tokens = []
        for c in self.commands:
            tokens.append((Token.Command, "%s\n" % c))
        print_tokens(tokens)

    def do_create(self, arguments):
        self.do_close_wallet()
        item = get_arg(arguments)
        if self.Wallet:
            self.do_close_wallet()

        if item and item == 'wallet':

            path = get_arg(arguments, 1)

            if path:

                if os.path.exists(path):
                    print("File already exists")
                    return

                passwd1 = prompt("[Password 1]> ", is_password=True)
                passwd2 = prompt("[Password 2]> ", is_password=True)

                if passwd1 != passwd2 or len(passwd1) < 1:
                    print("please provide matching passwords that are at least 1 characters long")
                    return

                self.Wallet = Wallet.Create(path=path, password=passwd1)
                print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))

                try:
                    self.Wallet = Wallet.Create(path=path, password=passwd1)
                    print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))
                except Exception as e:
                    print("Exception creating wallet: %s " % e)
                    self.Wallet = None
                    if os.path.isfile(path):
                        try:
                            os.remove(path)
                        except Exception as e:
                            print("Could not remove {}: {}".format(path, e))
                return

            else:
                print("Please specify a path")

    def do_open(self, arguments):
        if self.Wallet:
            self.do_close_wallet()

        item = get_arg(arguments)

        if item and item == 'wallet':

            path = get_arg(arguments, 1)

            if path:

                if not os.path.exists(path):
                    print("wallet file not found")
                    return

                passwd = prompt("[Password]> ", is_password=True)
                self.Wallet = Wallet.Open(path, passwd)

                try:
                    self.Wallet = Wallet.Open(path, passwd)


                    print("Opened wallet at %s" % path)
                except Exception as e:
                    print("could not open wallet: %s " % e)

            else:
                print("Please specify a path")
        else:
            print("please specify something to open")

    def do_close_wallet(self):
        if self.Wallet:
            path = self.Wallet._path
            self.Wallet = None
            print("closed wallet %s " % path)


    def show_wallet(self, arguments):

        if not self.Wallet:
            print("please open a wallet")
            return

        item = get_arg(arguments)

        if not item:
            print("Wallet %s " % json.dumps(self.Wallet.ToJson(), indent=4))
            return

        else:
            print("wallet: '{}' is an invalid parameter".format(item))

    def do_import(self, arguments):
        item = get_arg(arguments)

        if not item:
            print("please specify something to import")
            return
        else:
            print("Import of '%s' not implemented" % item)


    def do_export(self, arguments):
        item = get_arg(arguments)

        if item == 'wif':
            if not self.Wallet:
                return print("please open a wallet")

            address = get_arg(arguments, 1)
            if not address:
                return print("Please specify an address")

            passwd = prompt("[Wallet Password]> ", is_password=True)
            if not self.Wallet.ValidatePassword(passwd):
                return print("Incorrect password")

            keys = self.Wallet.GetKeys()
            for key in keys:
                if key.GetAddress() == address:
                    export = key.Export()
                    print("WIF key export: %s" % export)
            return

        print("Command export %s not found" % item)


    def do_send(self, arguments):
        if not self.Wallet:
            print("please open a wallet")
            return False
        if len(arguments) < 3:
            print("Not enough arguments")
            return False


        to_send = get_arg(arguments)
        assetId = get_asset_id(to_send)
        if assetId is None:
            print("Asset id not found")
            return False

        address_to = get_arg(arguments, 1)
        amount = get_arg(arguments, 2)
        address_from=self.Wallet._accounts[0]["account"].GetAddress()

        res = self.Wallet.send(addressFrom=address_from,addressTo=address_to,amount=amount,assetId=assetId)
        TX_RECORD.save(tx_id=res[1],asset_type=assetId,address_from=address_from,
                       address_to=address_to,value=amount,state=res[0])
        return


    def show_tx(self, args):
        item = get_arg(args)
        if item is not None:
            try:
                pprint.pprint (show_tx(item))
            except Exception as e:
                print("Could not find transaction with id %s " % item)
        else:
            tx_records=TX_RECORD.query(self.Wallet._accounts[0]["account"].GetAddress())
            for item in tx_records:
                print(item.to_json())

    def parse_result(self, result):
        if len(result):
            commandParts = [s for s in result.split()]
            return commandParts[0], commandParts[1:]
        return None, None

    def run(self):
        tokens = [(Token.Neo, 'TRINITY'), (Token.Default, ' cli. Type '),
                  (Token.Command, "'help' "), (Token.Default, 'to get started')]

        #print_tokens(tokens,self.token_style)
        print("\n")

        while self.go_on:
            try:
                result = prompt("trinity>",
                                history=self.history,
                                get_bottom_toolbar_tokens=self.get_bottom_toolbar,
                                style=self.token_style,
                                # refresh_interval=15
                                )
            except EOFError:
                return self.quit()
            except KeyboardInterrupt:
                self.quit()
                continue

            try:
                command, arguments = self.parse_result(result)

                if command is not None and len(command) > 0:
                    command = command.lower()

                    if command == 'quit' or command == 'exit':
                        self.quit()
                    elif command == 'help':
                        self.help()
                    elif command == 'wallet':
                        self.show_wallet(arguments)
                    elif command is None:
                        print('please specify a command')
                    elif command == 'create':
                        self.do_create(arguments)
                    elif command == 'close':
                        self.do_close_wallet()
                    elif command == 'open':
                        self.do_open(arguments)
                    elif command == 'export':
                        self.do_export(arguments)
                    elif command == 'wallet':
                        self.show_wallet(arguments)
                    elif command == 'send':
                        self.do_send(arguments)
                    elif command == 'tx':
                        self.show_tx(arguments)

                    else:
                        print("command %s not found" % command)

            except Exception as e:

                print("could not execute command: %s " % e)
                traceback.print_stack()
                traceback.print_exc()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-m", "--mainnet", action="store_true", default=False,
                        help="Use MainNet instead of the default TestNet")
    parser.add_argument("-p", "--privnet", action="store_true", default=False,
                        help="Use PrivNet instead of the default TestNet")

    args = parser.parse_args()

    if args.mainnet:
        settings.setup_mainnet()
    elif args.privnet:
        settings.setup_privnet()
    else:
        settings.setup_testnet()

    cli = PromptInterface()
    cli.run()

if __name__ == "__main__":
    main()
