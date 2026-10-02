# 계좌 여력 원천 조회 최종 재리뷰 샘플 성능

2026-10-02 19:14 KST. 격리 후보·baseline 각각 1,000 batch를 3회 수행했다. Mock transport와 고정 action fixture이며 실제 API/정책 발행은 0회다. Baseline은 원 Git 1930ac82, source hash와 원 clock/hash/수량 digest는 아래 원 측정에 보존한다.

```json
{
  "runs": {
    "baseline": [
      {
        "action_labels_are_fixed_fixture_not_machine_policy_performance": true,
        "actual_api_calls": 0,
        "counts": {
          "logical": 18000,
          "physical_http": 15000,
          "required_http": 5000
        },
        "cpu_sec": 2.078280631,
        "diagnostic_rows": 0,
        "evidence_digest": "c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8",
        "peak_rss_kib": 306048,
        "policy_writes": 0,
        "source_sha256": {
          "handlers": "9e7cfc7f139ceaf23a0c8bc9e5ace65b61103edbbac144340356284e5223cb0c",
          "orders": "82a46f54a89ace34ffc819d7d96b013d095d116bc7689ac48729e17584d84841",
          "utils": "e17ee1651f1e702fe8fa64f872a1498d80eb7b4e795cd1e5d0d52e976ffcfa26"
        },
        "transport": "mocked_zero_network_latency_real_parser",
        "usable_capacity_by_fixed_action": {
          "BLOCK": 1000,
          "ENTER_NOW": 1000,
          "RECHECK": 1000
        },
        "wall_sec": 2.078842959017493
      },
      {
        "action_labels_are_fixed_fixture_not_machine_policy_performance": true,
        "actual_api_calls": 0,
        "counts": {
          "logical": 18000,
          "physical_http": 15000,
          "required_http": 5000
        },
        "cpu_sec": 2.070391077,
        "diagnostic_rows": 0,
        "evidence_digest": "c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8",
        "peak_rss_kib": 306048,
        "policy_writes": 0,
        "source_sha256": {
          "handlers": "9e7cfc7f139ceaf23a0c8bc9e5ace65b61103edbbac144340356284e5223cb0c",
          "orders": "82a46f54a89ace34ffc819d7d96b013d095d116bc7689ac48729e17584d84841",
          "utils": "e17ee1651f1e702fe8fa64f872a1498d80eb7b4e795cd1e5d0d52e976ffcfa26"
        },
        "transport": "mocked_zero_network_latency_real_parser",
        "usable_capacity_by_fixed_action": {
          "BLOCK": 1000,
          "ENTER_NOW": 1000,
          "RECHECK": 1000
        },
        "wall_sec": 2.070437074988149
      },
      {
        "action_labels_are_fixed_fixture_not_machine_policy_performance": true,
        "actual_api_calls": 0,
        "counts": {
          "logical": 18000,
          "physical_http": 15000,
          "required_http": 5000
        },
        "cpu_sec": 2.079532398,
        "diagnostic_rows": 0,
        "evidence_digest": "c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8",
        "peak_rss_kib": 306096,
        "policy_writes": 0,
        "source_sha256": {
          "handlers": "9e7cfc7f139ceaf23a0c8bc9e5ace65b61103edbbac144340356284e5223cb0c",
          "orders": "82a46f54a89ace34ffc819d7d96b013d095d116bc7689ac48729e17584d84841",
          "utils": "e17ee1651f1e702fe8fa64f872a1498d80eb7b4e795cd1e5d0d52e976ffcfa26"
        },
        "transport": "mocked_zero_network_latency_real_parser",
        "usable_capacity_by_fixed_action": {
          "BLOCK": 1000,
          "ENTER_NOW": 1000,
          "RECHECK": 1000
        },
        "wall_sec": 2.079734868952073
      }
    ],
    "candidate": [
      {
        "action_labels_are_fixed_fixture_not_machine_policy_performance": true,
        "actual_api_calls": 0,
        "counts": {
          "logical": 18000,
          "physical_http": 6000,
          "required_http": 5000
        },
        "cpu_sec": 2.144312672,
        "diagnostic_rows": 18000,
        "evidence_digest": "c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8",
        "peak_rss_kib": 307356,
        "policy_writes": 0,
        "source_sha256": {
          "handlers": "42cba5b93db1e5a8d058a7013004bec7c4019f3fba0004101e78faaed85fe718",
          "orders": "bd09ec53877feab2aafd8dbacf3ec4a0ec7181006a948bb60b9e399588688e5f",
          "utils": "da3b0b82a0221b4cf40fbcf46f0edde5efd7a975547c2bc2e8e76b032bd1146b"
        },
        "transport": "mocked_zero_network_latency_real_parser",
        "usable_capacity_by_fixed_action": {
          "BLOCK": 1000,
          "ENTER_NOW": 1000,
          "RECHECK": 1000
        },
        "wall_sec": 2.1507404319709167
      },
      {
        "action_labels_are_fixed_fixture_not_machine_policy_performance": true,
        "actual_api_calls": 0,
        "counts": {
          "logical": 18000,
          "physical_http": 6000,
          "required_http": 5000
        },
        "cpu_sec": 2.125936564,
        "diagnostic_rows": 18000,
        "evidence_digest": "c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8",
        "peak_rss_kib": 307368,
        "policy_writes": 0,
        "source_sha256": {
          "handlers": "42cba5b93db1e5a8d058a7013004bec7c4019f3fba0004101e78faaed85fe718",
          "orders": "bd09ec53877feab2aafd8dbacf3ec4a0ec7181006a948bb60b9e399588688e5f",
          "utils": "da3b0b82a0221b4cf40fbcf46f0edde5efd7a975547c2bc2e8e76b032bd1146b"
        },
        "transport": "mocked_zero_network_latency_real_parser",
        "usable_capacity_by_fixed_action": {
          "BLOCK": 1000,
          "ENTER_NOW": 1000,
          "RECHECK": 1000
        },
        "wall_sec": 2.1259797870879993
      },
      {
        "action_labels_are_fixed_fixture_not_machine_policy_performance": true,
        "actual_api_calls": 0,
        "counts": {
          "logical": 18000,
          "physical_http": 6000,
          "required_http": 5000
        },
        "cpu_sec": 2.142245081,
        "diagnostic_rows": 18000,
        "evidence_digest": "c9f6cf7beb16782af5bb157fb1d5df4ac0d51fedc49a3fd486dee00a170f82f8",
        "peak_rss_kib": 307372,
        "policy_writes": 0,
        "source_sha256": {
          "handlers": "42cba5b93db1e5a8d058a7013004bec7c4019f3fba0004101e78faaed85fe718",
          "orders": "bd09ec53877feab2aafd8dbacf3ec4a0ec7181006a948bb60b9e399588688e5f",
          "utils": "da3b0b82a0221b4cf40fbcf46f0edde5efd7a975547c2bc2e8e76b032bd1146b"
        },
        "transport": "mocked_zero_network_latency_real_parser",
        "usable_capacity_by_fixed_action": {
          "BLOCK": 1000,
          "ENTER_NOW": 1000,
          "RECHECK": 1000
        },
        "wall_sec": 2.1428377650445327
      }
    ]
  },
  "medians": {
    "baseline": {
      "wall_sec": 2.078842959017493,
      "cpu_sec": 2.078280631,
      "peak_rss_kib": 306048
    },
    "candidate": {
      "wall_sec": 2.1428377650445327,
      "cpu_sec": 2.142245081,
      "peak_rss_kib": 307368
    }
  },
  "ratios": {
    "wall_sec": 1.0307838577942825,
    "cpu_sec": 1.0307775807780215
  },
  "rss_delta_mib": 1.2890625,
  "source_and_coverage_equal": true,
  "engineering_gate": true
}
```
