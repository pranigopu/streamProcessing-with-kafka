> [Previous: Setting Up](../setting-up.md)

<h1>INSTALLATION VERIFICATION</h1>

---

**Contents**:

- [Verify if all containers have been deployed](#verify-if-all-containers-have-been-deployed)
- [Verify if Kafka UI is working (enter in browser)](#verify-if-kafka-ui-is-working-enter-in-browser)

---

# Verify if all containers have been deployed
```
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
```

Expected output:

![](./resources/all-deployed-docker-containers.png)

# Verify if Kafka UI is working (enter in browser)
```
http://localhost:8080/
```

Expected outputs:

![](./resources/kafka-ui-after-deployment--topics.png)

![](./resources/kafka-ui-after-deployment--consumers.png)

![](./resources/kafka-ui-after-deployment--brokers.png)

---

> [Next: Publish Topics for Testing](./publish-topics-for-testing.md)