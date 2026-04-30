# A2A-040: Compute & Execution

**Version:** 1.0 | **Status:** Stable

## 1. Scope
Defines how A2A-compliant systems request, schedule, execute, verify, and report computational workloads. Extends the protocol from agent messaging into actual workload execution — sandboxed compute, container jobs, GPU tasks, distributed inference, and proof of execution.

## 2. Compute Roles
- `COMPUTE_REQUESTER` — Agent or orchestrator requesting compute
- `COMPUTE_PROVIDER` — Organization or node offering capacity
- `SCHEDULER` — Matches workloads to available compute
- `EXECUTION_RUNTIME` — Runs the workload
- `VERIFICATION_AGENT` — Verifies outputs, receipts, or proofs

## 3. Workload Types
```
LLM_INFERENCE  BATCH_ANALYSIS  TOOL_EXECUTION  DATA_TRANSFORMATION
MODEL_TRAINING  MODEL_FINE_TUNING  SIMULATION  CODE_EXECUTION  GPU_RENDERING
```

## 4. Resource Classes
```
RC_MICRO  RC_STANDARD  RC_MEMORY_HEAVY  RC_CPU_HEAVY
RC_GPU_SMALL  RC_GPU_LARGE  RC_DISTRIBUTED
```

## 5. Runtime Isolation
- `CONTAINER`, `MICROVM` (recommended for untrusted), `WASM_SANDBOX`, `PROCESS_ISOLATION`

## 6. Sandbox Profiles
```
NO_NETWORK  READ_ONLY_INPUT  TEMP_STORAGE_ONLY  NO_PERSISTENCE  APPROVED_EGRESS_ONLY
```

## 7. Execution Lifecycle
```
SUBMITTED → SCHEDULED → RESOURCES_RESERVED → EXECUTION_STARTED
  → EXECUTION_COMPLETED → RESULT_VERIFIED → RECEIPT_EMITTED → SETTLEMENT_RELEASED
```

## 8. Proof of Execution
A provider MAY emit an execution proof containing: `WORKLOAD_ID`, `RUNTIME_ID`, `START_TIMESTAMP`, `END_TIMESTAMP`, `INPUT_HASH`, `OUTPUT_HASH`, `ENVIRONMENT_HASH`, `PROVIDER_SIGNATURE`.

## 9. Metering
- `EXECUTION_TIME_MS`, `CPU_SECONDS`, `GPU_SECONDS`, `MEMORY_PEAK_MB`, `TOKENS_PROCESSED`, `IO_BYTES`

## 10. Compute Receipt Example
```json
{
  "workload_id": "WL-INF-2031",
  "receipt_status": "COMPLETED",
  "resource_class": "RC_GPU_SMALL",
  "metering": { "gpu_seconds": 1.8, "tokens_processed": 3821 },
  "output_hash": "sha256:...",
  "result_status": "SUCCESS"
}
```
