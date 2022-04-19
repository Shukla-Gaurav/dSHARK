import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import argparse
import numpy as np

import tritonclient.http as httpclient
from tritonclient.utils import InferenceServerException


torch.manual_seed(0)

def prepare_sentence_tokens(tokenizer, sentence):
    return torch.tensor([tokenizer.encode(sentence)])

tokenizer = AutoTokenizer.from_pretrained("albert-base-v2")
test_input = prepare_sentence_tokens(
        tokenizer, "this project is very interesting")

print(test_input, test_input.dtype)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u',
                        '--url',
                        type=str,
                        required=False,
                        default='localhost:8000',
                        help='Inference server URL. Default is localhost:8000.')
    FLAGS = parser.parse_args()

    # For the HTTP client, need to specify large enough concurrency to
    # issue all the inference requests to the server in parallel. For
    # this example we want to be able to send 2 requests concurrently.
    try:
        concurrent_request_count = 2
        triton_client = httpclient.InferenceServerClient(
            url=FLAGS.url, concurrency=concurrent_request_count)
    except Exception as e:
        print("channel creation failed: " + str(e))
        sys.exit(1)

    print('Sending request to nonbatching model: IN0 = {}'.format(test_input))

    inputs = [ httpclient.InferInput('IN0', [1,7], "INT64") ]

    inputs[0].set_data_from_numpy(np.array(test_input))
    result = triton_client.infer('dshark_bert', inputs)

    print('Response: {}'.format(result.get_response()))
    print('OUT0 = {}'.format(result.as_numpy('OUT0')))
