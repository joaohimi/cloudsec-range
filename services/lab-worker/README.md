# Lab Worker Boundary (reserved)

This service is intentionally not implemented in milestone 0.

It will eventually run disposable lab workloads under a separate identity and network boundary. It must not mount the Docker socket into vulnerable workloads, inherit app secrets, mount the learner's home directory, or receive long-lived AWS credentials.

See `docs/security/lab-safety-model.md` before implementation.
