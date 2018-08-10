#!/usr/bin/env python
import argparse
import json
import pprint
import traceback
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import print_tokens
from prompt_toolkit.styles import style_from_dict
from prompt_toolkit.token import Token
import os
import sys
pythonpath = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(pythonpath)
from lightwallet.Utils import get_arg,get_asset_id
from lightwallet.Settings import settings
from lightwallet.wallet import Wallet

from lightwallet.UserPreferences import preferences
import binascii

FILENAME_PROMPT_HISTORY = os.path.join(settings.DIR_CURRENT, '.prompt.py.history')

class PromptInterface(object):
    """
    class PromptInterface
    handle the wallet cli commands
    """

    commands = [
                'help',
                'quit',
                'create wallet {path}',
                'open wallet {path}',
                'close',
                'wallet',
                'send {asset} {address} {amount}',
                'history',
                'lock cli',
                'unlock cli'
                ]
    go_on = True
    Wallet=None
    history = FileHistory(FILENAME_PROMPT_HISTORY)
    locked = False

    def __init__(self):

        self.token_style = style_from_dict({
            Token.Command: preferences.token_style['Command'],
            Token.Neo: preferences.token_style['Neo'],
            Token.Default: preferences.token_style['Default'],
            Token.Number: preferences.token_style['Number'],
        })


    def get_bottom_toolbar(self, cli=None):
        """

        :param cli:
        :return:
        """

        out = []
        try:
            out = [
                (Token.Command, '[%s]' % (settings.NET_NAME if not PromptInterface.locked else settings.NET_NAME + " (Locked) ")),

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
        """

        :param arguments:
        :return:
        """
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
        """

        :param arguments:
        :return:
        """

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
        """

        :return:
        """
        if self.Wallet:
            path = self.Wallet._path
            self.Wallet = None
            print("closed wallet %s " % path)


    def show_wallet(self, arguments):
        """

        :param arguments:
        :return:
        """


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
        """

        :param arguments:
        :return:
        """

        item = get_arg(arguments)

        if not item:
            print("please specify something to import")
            return
        else:
            print("Import of '%s' not implemented" % item)


    def do_export(self, arguments):
        """

        :param arguments:
        :return:
        """
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
        """

        :param arguments:
        :return:
        """

        if not self.Wallet:
            print("please open a wallet")
            return False
        if len(arguments) < 3:
            print("Not enough arguments")
            return False


        assetId = get_arg(arguments).upper()
        address_to = get_arg(arguments, 1)
        amount = float(get_arg(arguments, 2))
        gaslimit = int(get_arg(arguments,3)) if get_arg(arguments,3) else 25600
        gasprice = int(get_arg(arguments,4)) if get_arg(arguments, 4) else None

        if assetId == "ETH":

            try:
                res = self.Wallet.send_eth(address_to, amount, gaslimit)
                print("txid: 0x"+res)
            except Exception as e:
                print("send failed %s" %e)
        elif assetId == "TNC":

            try:
                res = self.Wallet.send_erc20(assetId, address_to, amount, gaslimit, gasprice)
                print("txid: 0x" +res)
            except Exception as e:
                print("send failed %s" % e)

        else:
            pass
        return

    def unlock(self, args):
        """

        :param args:
        :return:
        """

        item = get_arg(args)
        if item == "cli":
            if PromptInterface.locked:
                passwd = prompt("[Wallet Password]> ", is_password=True)
                if not self.Wallet.ValidatePassword(passwd):
                    print("Incorrect password")
                    return None
                PromptInterface.locked = False
                print("cli unlocked")
            else:
                print("cli not in locked mode")
        elif item == "wallet":
            pass
        else:
            print("please spacify unlock item [cli/wallet]")
        return None

    def do_lock(self, args):
        """

        :param args:
        :return:
        """
        item = get_arg(args)
        if item == "cli":
            if PromptInterface.locked:
                print("cli now is in locked mode")
            else:
                if self.Wallet:
                    PromptInterface.locked = True
                    print("lock cli with wallet %s" %self.Wallet.name)
                else:
                    print("No opened wallet")
        elif item == "wallet":
            pass
        else:
            print("please spacify lock item [cli/wallet]")
        return None

    def show_tx(self, args):
        """

        :param args:
        :return:
        """
        history = self.Wallet.query_history()
        for item in history:
            print("*"*20)
            print(item)
        return

    def parse_result(self, result):
        """

        :param result:
        :return:
        """
        if len(result):
            commandParts = [s for s in result.split()]
            return commandParts[0], commandParts[1:]
        return None, None

    def handle_commands(self,command, arguments):
        """

        :param command:
        :param arguments:
        :return:
        """
        if command == "unlock":
            self.unlock(arguments)
        elif command == 'quit' or command == 'exit':
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
        elif command == 'history':
            self.show_tx(arguments)
        elif command == "lock":
            self.do_lock(arguments)
        else:
            print("command %s not found" % command)

    def handle_locked_command(self, command, arguments):
        """

        :param command:
        :param arguments:
        :return:
        """
        if command == "unlock":
            self.unlock(arguments)

        else:
            print("cli is in locked mode please unlock cli via 'unlock cli'")
            return None

    def run(self):
        """

        :return:
        """
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
            # try:
            #     command, arguments = self.parse_result(result)
            #
            #     if command is not None and len(command) > 0:
            #         command = command.lower()
            #
            #         if self.locked:
            #             self.handle_locked_command(command, arguments)
            #             continue
            #
            #         else:
            #             self.handle_commands(command, arguments)
            #
            # except Exception as e:
            #
            #     print("could not execute command: %s " % e)
            #     traceback.print_stack()
            #     traceback.print_exc()
            command, arguments = self.parse_result(result)

            if command is not None and len(command) > 0:
                command = command.lower()

                if PromptInterface.locked:
                    self.handle_locked_command(command, arguments)
                    continue

                else:
                    self.handle_commands(command, arguments)


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
