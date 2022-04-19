# Triton Server With DSHARK Backend

To set up a triton server with a dshark backend, first build the docker image from Dockerfile.compose

```
docker build -t tritonserver_custom -f Dockerfile.compose .
```

Next run the docker container

```
docker run -it --net=host -v/path/to/dSHARK/inference/docker_setup/model_repos:/models  tritonserver_custom:latest tritonserver --model-repository=/models
```

next run the client script.  you may need to pip install some packages

```
python3 client/bert_client.py
```

your results should look like:
```
tensor([[   2,   48,  669,   25,  253, 4883,    3]]) torch.int64
Sending request to nonbatching model: IN0 = tensor([[   2,   48,  669,   25,  253, 4883,    3]])
Response: {'model_name': 'dshark_bert', 'model_version': '1', 'outputs': [{'name': 'OUT0', 'datatype': 'FP32', 'shape': [1, 2], 'parameters': {'binary_data_size': 8}}]}
OUT0 = [[-0.04375369  0.5148138 ]]
```