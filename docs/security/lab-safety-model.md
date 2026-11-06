# Lab Safety Model

## Security objective

The lab platform must not turn a training vulnerability into a compromise of the CloudSec Range application, host, personal data or third-party systems.

## Mandatory controls before executable labs are enabled

- Separate app, data and lab network planes.
- Separate lab worker identity and runtime.
- No Docker socket mount into vulnerable containers.
- No host filesystem mounts except explicitly reviewed read-only fixture paths.
- No SSH agent, cloud CLI profile, browser profile or personal credentials in lab environments.
- Deny outbound network access by default; explicit per-lab allowlists only.
- Use synthetic data and disposable credentials.
- Use allowlisted, versioned and scanned lab images.
- Set CPU, memory, PID, disk, wall-clock and concurrency limits.
- Use disposable VMs for kernel exploits, privilege escalation or risky operating-system behavior.
- Require explicit target identifiers for offensive exercises.
- Do not allow public IP targets or arbitrary URLs by default.
- Log start, stop, commands/events as appropriate, policy decisions and cleanup result.
- Provide an emergency stop and cleanup workflow.
- Verify that resources are removed; report cleanup failures as incidents.

## AWS sandbox controls

- Dedicated AWS account or organization member account.
- Short-lived role sessions; no long-lived keys stored in the platform.
- Region, service, resource-type and naming/tag allowlists.
- Deny sensitive actions unless a scenario explicitly requires them and the control plane approves them.
- Budget alerts are supplementary; they are not a real-time kill switch.
- Automated expiration and independent orphan-resource sweeps.
- CloudTrail auditing and security alerts.
- Never use production accounts or personal data for vulnerable labs.

## Current state

No attack execution is enabled in milestone 0. The above are release gates for the future Lab Engine and Attack/Defense Range.
