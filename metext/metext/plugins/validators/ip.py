import ipaddress

from metext.plugin_base import BaseValidator


class IPv4AddressValidator(BaseValidator):
    PLUGIN_NAME = "ipv4"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        try:
            ipaddress.IPv4Address(_input)
            return True
        except:
            return False


class IPv6AddressValidator(BaseValidator):
    PLUGIN_NAME = "ipv6"

    @classmethod
    def run(cls, _input, **kwargs) -> bool:
        try:
            ipaddress.IPv6Address(_input)
            return True
        except:
            return False
