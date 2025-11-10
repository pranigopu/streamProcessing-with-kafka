> [Previous: Setting Up](./setting-up.md) :: [Next: Publish Topics for Testing](./publish-topics-for-testing.md)

<h1>INSTALLATION VERIFICATION</h1>

---

**Contents**:

- [Verify if all containers have been deployed](#verify-if-all-containers-have-been-deployed)
- [Verify if Kafka UI is working (via browser)](#verify-if-kafka-ui-is-working-via-browser)

---

# Verify if all containers have been deployed
```
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
```

Expected output:

![](./resources/all-deployed-docker-containers.png)

# Verify if Kafka UI is working (via browser)
```
http://localhost:8080/
```

Expected outputs:

*Topics*

![](./resources/kafka-ui-after-deployment--topics.png)

*Consumers*

![](./resources/kafka-ui-after-deployment--consumers.png)

*Brokers*

![](./resources/kafka-ui-after-deployment--brokers.png)