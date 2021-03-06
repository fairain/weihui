import json

from Utils import testload, exception
from Utils.common import decode


class ResponseObject(object):

    def __init__(self, resp_obj):
        """ initialize with a requests.Response object
        @param (requests.Response instance) resp_obj
        """
        self.resp_obj = resp_obj


    def parsed_body(self):
        try:
            return self.resp_obj.json()
        except ValueError:
            return decode(self.resp_obj.text)

    def parsed_dict(self):
        return {
            'status_code': self.resp_obj.status_code,
            'headers': self.resp_obj.headers,
            'body': self.parsed_body()
        }

    def extract_field(self, field):
        """ extract field from requests.Response
        @param (str) field of requests.Response object, and may be joined by delimiter
            "status_code"
            "content"
            "headers.content-type"
            "content.person.name.first_name"
        """
        try:
            return json.loads(self.resp_obj['response_msg']).get(field)

        except AttributeError:
            raise exception.ParseResponseError("failed to extract bind variable in response!")

    def extract_response(self, extract_binds):
        """ extract content from requests.Response
        @param (list) extract_binds
            [
                {"resp_status_code": "status_code"},
                {"resp_headers_content_type": "headers.content-type"},
                {"resp_content": "content"},
                {"resp_content_person_first_name": "content.person.name.first_name"}
            ]
        @return (list) variable binds list
        """
        extracted_variables_mapping_list = []

        for extract_bind in extract_binds:
            for key, field in extract_bind.items():
                if not isinstance(field, testload.string_type):
                    raise exception.ParamsError("invalid extract_binds in testcase extract_binds!")

                extracted_variables_mapping_list.append(
                    {key: self.extract_field(field)}
                )
        return extracted_variables_mapping_list

    def validate(self, validators):
        """ Bind named validators to value within the context.
        @param (list) validators
            [
                {"check": "status_code", "comparator": "eq", "expected": 201},
                {"check": "resp_body_success", "comparator": "eq", "expected": True}
            ]
        @param (dict) variables_mapping
            {
                "resp_body_success": True
            }
        @return (list) content differences
            [
                {
                    "check": "status_code",
                    "comparator": "eq", "expected": 201, "value": 200
                }
            ]
        """
        for validator_dict in validators:
            check_item = validator_dict.get("check")
            if not check_item:
                raise exception.ParamsError("invalid check item in testcase validators!")

            if "expected" not in validator_dict:
                raise exception.ParamsError("expected item missed in testcase validators!")

            expected = validator_dict.get("expected")
            comparator = validator_dict.get("comparator", "eq")

            try:
                validator_dict["actual_value"] = self.extract_field(check_item)
            except exception.ParseResponseError:
                raise exception.ParseResponseError("failed to extract check item in response!")

            testload.match_expected(
                validator_dict["actual_value"],
                expected,
                comparator,
                check_item,
                self.resp_obj['response_msg']
            )

        return True


