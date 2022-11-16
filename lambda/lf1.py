import json
import urllib.parse
import boto3
from datetime import datetime
from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth

host = 'search-photos-fi6tkdtpua4mm3lpfuebg26sdi.us-east-1.es.amazonaws.com'
region = 'us-east-1'
index_name = 'photo'

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region)
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
opensearch = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

def lambda_handler(event, context):
    print("Hello")
    print("Received event: " + json.dumps(event))
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        today = datetime.now()

        header = s3.head_object(Bucket=bucket, Key=key)
        if 'x-amz-meta-customlabels' in header['ResponseMetadata']['HTTPHeaders']:
            custom_labels = header['ResponseMetadata']['HTTPHeaders']['x-amz-meta-customlabels'].split(',')
            print("detected custom labels : {}".format(custom_labels))
        else:
            custom_labels = []
    

        response = rekognition.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':key}},
            MaxLabels=10)
        print("rekognition response : {}".format(response))
        if 'Labels' in response:
            labels = [x['Name'] for x in response['Labels']]
            print("detected labels : {}".format(labels))
        else:
            labels = []
            
        total_labels = custom_labels + labels
        clean_labels = []
        if total_labels:
            for label in total_labels:
                clean_label = ''.join(x for x in label if x.isalpha()).lower()
                clean_labels.append(clean_label)
                
            opensearch_id = datetime.now().strftime("%Y%m%d%H%M%S%f")
            document = {
                    'label': ",".join(clean_labels), 
                    's3_path': "https://{}.s3.amazonaws.com/{}".format(bucket, key)
                }
            response = opensearch.index(
                index = index_name,
                body = document,
                id = opensearch_id,
                refresh = True
            )
            print("Adding to OpenSearch : index : {}, body : {}, id : {}".format(index_name, document, opensearch_id))
    
        return {
            "objectKey": key,
            "bucket": bucket,
            'createdTimestamp': today.isoformat(),
            "labels": total_labels,
        }
    except Exception as e:
        print(e)
        print('Error processing object {} from bucket {}.'.format(key, bucket))
        raise e