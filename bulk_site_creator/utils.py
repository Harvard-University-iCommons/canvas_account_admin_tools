import logging

from botocore.exceptions import ClientError


# https://boto3.amazonaws.com/v1/documentation/api/latest/guide/dynamodb.html#batch-writing
def batch_write_item(table, items: list[dict]):
    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
    except ClientError as e:
        logging.error(e.response["Error"]["Message"])
