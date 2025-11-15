<h1>KAFKA CONTROLLER</h1>

---

**Contents**:

- [What is it?](#what-is-it)

---

# What is it?
Kafka controller (also called controller broker) is a Kafka service that is active only on one broker in a Kafka cluster, i.e. if we have a cluster of N brokers then there will be only one broker that is the controller at a time. The process of promoting a broker to be the active controller is called "Kafka Controller Election". Note that it runs on every broker in a Kafka cluster, but only one can be active (elected) at any point in time. In a Kafka cluster, one of the brokers serves as the controller (i.e. the broker in which the controller broker is active), which is responsible for managing the states of partitions and replicas and for performing administrative tasks like reassigning partitions, monitoring broker liveness, and handling broker failures. It is the "brain" of the cluster, ensuring partitions and replicas are in a consistent state. This role is vital for self-healing, as the controller handles fails to minimise downtime.  

> **References**:
> 
> - [*Whereabouts of Kafka Controller* by Sun, **sunil-dang.medium.com**](https://sunil-dang.medium.com/whereabouts-of-kafka-controller-6708b0627141)
> - [*Controller Broker*, **jaceklaskowski.gitbooks.io/apache-kafka/content/**](https://jaceklaskowski.gitbooks.io/apache-kafka/content/kafka-controller.html)