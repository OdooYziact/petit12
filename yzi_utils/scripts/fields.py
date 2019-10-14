# -*- coding: utf-8 -*-

# from odoo import models, fields, api, _


def get_fields_from_recordset(recordset, cols=4, fields=['name', 'value'], default_value=""):
    """
    Retourne une liste des champs spécifiés pour le recordset groupée par ligne de n éléments

    [
        [
            [field1, field2], [field1, field2], [field1, field2]...
        ],
        [
            [field1, field2], [field1, field2], [field1, field2]...
        ]
    ]

    :param recordset:
    :param cols:
    :param fields:
    :param default_value:
    :return: fields list or []
    """
    results = []

    if not any([field for field in fields if field in recordset]):
        return results

    # return list
    # records = [[record[field] for field in fields] for record in recordset]

    # return dict
    records = [{field: record[field] for field in fields} for record in recordset]
    res = len(records) % cols

    if res != 0:
        records += [{field: default_value for field in fields}] * (cols - res)
        # return list
        # records += [[default_value, default_value]] * (cols - res)


    results = [records[x:x + cols] for x in range(0, len(records), cols)]

    return results