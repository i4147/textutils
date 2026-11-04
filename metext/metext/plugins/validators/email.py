from email_validator import validate_email

from metext.plugin_base import BaseValidator


class EmailValidator(BaseValidator):
    PLUGIN_NAME = "email"

    @classmethod
    def run(cls, _input: str, **kwargs) -> bool:
        # return RE_EMAIL.match(_input) is not None # too slow
        try:
            validate_email(_input, check_deliverability=True)
            return True
        except:
            return False
