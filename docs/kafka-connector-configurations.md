> [Previous: Setting Up](./setting-up.md) :: [Next: Installation Verification](./installation-verification.md)

<h1>KAFKA CONNECTOR CONFIGURATIONS</h1>

---

# HTTP source connector configurations
**JSON**:

```json
{
  "name": "http-source",
  "config": {
    "connector.class": "io.confluent.connect.http.HttpSourceConnector",
    "topic.name.pattern": "orders",
    "url": "http://host.docker.internal:3000/orders",
    "http.offset.mode": "SIMPLE_INCREMENTING",
    "http.initial.offset": "1",
    "request.interval.ms": "86400000",
    "key.converter": "org.apache.kafka.connect.json.JsonConverter",
    "value.converter": "org.apache.kafka.connect.json.JsonConverter",
    "key.converter.schemas.enable": "false",
    "value.converter.schemas.enable": "false",
    "confluent.topic.bootstrap.servers": "kafka:29092",
    "confluent.topic.replication.factor": "1",
    "confluent.topic.security.protocol": "PLAINTEXT"
  }
}
```

Explanation for certain parameters:

- `"url": "http://host.docker.internal:3000/orders"`:
    - URL to which to make requests; the response is ingested as data
    - `host.docker.internal` is a special DNS name:
        - Used within Docker containers to refer to the host machine where Docker is running
        - Allows containers to access services or applications running directly on the host <br> *Rather than within another container*
        - Since the connector to be configured lives in a container, this DNS name is needed <br> *To make requests to the JSON server running on the host*
- `"http.offset.mode": "SIMPLE_INCREMENTING"`:
    - Indicates how offsets are computed and how requests are generated
    - If set to `SIMPLE_INCREMENTING`, the ${offset} used to generate requests is: <br> *Previous offset (or http.initial.offset) + Number of records in the response*
    - In this mode, `http.initial.offset` needs to be set to an integer value
- `"request.interval.ms": "86400000"`:
    - Time interval between 2 requests to the URL
    - Prevents the source connector from ingesting the same data repeatedly
    - The given interval is in milliseconds; 86400000 ms = 24 hours
- `"key.converter": "org.apache.kafka.connect.json.JsonConverter"`
    - Converts ingested data into JSON format

> **References**:
>
> - [*Configuration Reference for HTTP Source Connector for Confluent Platform*, **docs.confluent.io**](https://docs.confluent.io/kafka-connectors/http-source/current/configuration.html)
> - [*HTTP Source Connector for Confluent Cloud*, **docs.confluent.io/cloud/current**](https://docs.confluent.io/cloud/current/connectors/cc-http-source.html) (for example usage)
> - [*Kafka Connect Deep Dive – Converters and Serialization Explained*, **www.confluent.io/blog**](https://www.confluent.io/blog/kafka-connect-deep-dive-converters-serialization-explained/)