from json import load, dump, JSONEncoder
from pathlib import Path
from sys import path
from typing import List, Dict, Optional, Any
from os import PathLike, getcwd

from web3 import Web3
from web3.utils.datatypes import PropertyCheckingFactory
from hexbytes import HexBytes


class HexJsonEncoder(JSONEncoder):

    def default(self, obj):
        if isinstance(obj, HexBytes):
            return obj.hex()
        return super().default(obj)

class DeployContract:

    def __init__(self, settings_directory : Path = getcwd()):
        path.append(settings_directory)
        import settings
        networks = settings.networks

        development_network = networks["development"]
        if development_network["mode"]=="HTTP":
            server = "http://" + development_network["host"] + ":" + str(development_network["port"])
            self.w3 = Web3(Web3.HTTPProvider(server))

    def contract(self, smart_contract_name : str, build_contracts_directory : Path) -> PropertyCheckingFactory:
        contract_json_file = (build_contracts_directory / smart_contract_name).with_suffix('.json')

        with open(contract_json_file, "r") as smart_contract_build_file:
            json_object = load(smart_contract_build_file)
            bytecode = json_object["bytecode"]
            abi = json_object["abi"]
            smart_contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            return smart_contract

    def deploy_contract(self,
                        smart_contract_name : str,
                        parameters : List = [],
                        transaction_parameters : Dict[str, Optional[Any]] = {},
                        private_key : Optional[str] = None,
                        build_contracts_directory : Path = Path(".") / Path("build") / Path("contracts"),
                        deployed_directory : Path = Path(".") / Path("deployed")):

        smart_contract = self.contract(smart_contract_name, build_contracts_directory)
        smart_contract_constructor = smart_contract.constructor(*parameters)
        if private_key:
            from_account = transaction_parameters["from"]
            nonce = self.w3.eth.getTransactionCount(from_account)
            transaction_parameters["nonce"] = nonce
            tx_built = smart_contract_constructor.buildTransaction(transaction_parameters)
            tx_signed = self.w3.eth.account.signTransaction(tx_built, private_key=private_key)
            tx_hash = self.w3.eth.sendRawTransaction(tx_signed.rawTransaction)
        else:
            if transaction_parameters and not transaction_parameters.get("from", None):
                transaction_parameters["from"] = self.w3.personal.listAccounts[0]
            tx_hash = smart_contract_constructor.transact(transaction_parameters)
        tx_receipt = self.w3.eth.waitForTransactionReceipt(tx_hash)
        tx_dict = dict(tx_receipt)

        receipt_name = "receipt_%s" % smart_contract_name
        receipt_json_file = (deployed_directory / receipt_name).with_suffix('.json')

        with open(receipt_json_file, "w") as json_write_file:
            dump(tx_dict, json_write_file, cls=HexJsonEncoder, indent=4)
