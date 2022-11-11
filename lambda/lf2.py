from opensearchpy import OpenSearch, RequestsHttpConnection, AWSV4SignerAuth
import boto3
import json

host = 'search-photos-fi6tkdtpua4mm3lpfuebg26sdi.us-east-1.es.amazonaws.com'
region = 'us-east-1'
botID = '0YKQS6ZTGQ'
botAliasID = 'CJXWCG6WUW'
sessionID = 'session'
localeID = 'en_US'
index_name = 'photo'

credentials = boto3.Session().get_credentials()
auth = AWSV4SignerAuth(credentials, region)
opensearch = OpenSearch(
    hosts = [{'host': host, 'port': 443}],
    http_auth = auth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)
lex = boto3.client('lexv2-runtime')

def get_indiv_s3_paths(label):
    query = {
              'size': 100,
              'query': {
                'multi_match': {
                  'query': label,
                  'fields': ["label"]
                }
              }
            }
    response = opensearch.search(
        body = query,
        index = index_name
    )
    return [hits['_source']['s3_path'] for hits in response['hits']['hits']]

def get_s3_paths(labels):
  final_result = list()
  for label in labels:
    if label.endswith("s"):
      result = list(set(get_indiv_s3_paths(label)).union(set(get_indiv_s3_paths(label[:-1]))))
    else:
      result = get_indiv_s3_paths(label)
    final_result.append(result)
  final_result = list(set.intersection(*map(set,final_result)))
  return final_result[:12]

def get_labels(s3_path):
    query = {
              'size': 100,
              'query': {
                'multi_match': {
                  'query': s3_path,
                  'fields': ["s3_path"]
                }
              }
            }
    response = opensearch.search(
        body = query,
        index = index_name
    )
    return [hits['_source']['label'] for hits in response['hits']['hits']]

def process(item):
    return ''.join(x for x in item if x.isalpha()).lower()

def lambda_handler(event, context):
    print("event received : {}".format(event))
    print("context received : {}".format(context))

    result = {'results': []}
    full_query = event["queryStringParameters"]['q']
    full_query = full_query.replace("_", " ")
    print("full query : {}".format(full_query))
    response = lex.recognize_text(
            botId=botID,
            botAliasId=botAliasID,
            localeId=localeID,
            sessionId=sessionID,
            text=full_query)

    if response['sessionState']['intent']['name'] in ['SearchIntent',]:
        print("Lex : Search Intent - {}".format(full_query))
        l = [x.split(',') for x in full_query.split(" ")]
        queries = [process(item) for sublist in l for item in sublist if item not in ["and", ""]]
        if "show" in queries:
          queries.remove('show')
        if 'me' in queries:
          queries.remove('me')
        print("queries : {}".format(queries))
        images = get_s3_paths(queries)
        print("images : {}".format(images))
        for image in images:
            print("image : {}".format(image))
            labels = ",".join(get_labels(image)).split(',')
            print("labels : {}".format(labels))
            result['results'].append(
                {
                    'url': image,
                    'labels': labels
                }
            )
    else:
      print("Lex : Intent - {}".format(response['sessionState']['intent']['name']))
      return {
        'statusCode': 500,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(result),
        "isBase64Encoded": False
      } 
    print("result : {}".format(result))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(result),
        "isBase64Encoded": False
    } 