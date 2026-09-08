# Configuration Reference

Workforce Management Toolkit uses Pydantic V2 for configuration validation. The configuration is structured as nested models rather than a flat namespace.

## Base model (WFMBaseConfig)

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | str or None | None | Configuration name |
| `version` | str | "1.0.0" | Semantic version |
| `description` | str or None | None | Human-readable description |
| `tags` | list[str] | [] | Categorization tags |

## IntervalConfig

Time interval and timezone settings.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `interval_size` | int | required | Size of time interval |
| `interval_unit` | TimeInterval | required | Unit (minute, hour, day, week, month) |
| `business_start_hour` | int | 9 | Business start hour (0–23) |
| `business_end_hour` | int | 17 | Business end hour (0–23) |
| `working_days` | list[int] | [1,2,3,4,5] | Working days (1=Monday) |
| `timezone` | str | "UTC" | IANA timezone string |

## SLAConfig

Service level agreement targets.

| Parameter | Type | Default | Units | Range | Description |
|---|---|---|---|---|---|
| `target` | float | required | proportion | 0–1 | Target service level |
| `average_speed_of_answer` | float | required | seconds | >0 | Target ASA |
| `acceptable_service_level` | float | 0.90 | proportion | 0–1 | Acceptable SL |
| `minimum_service_level` | float | 0.95 | proportion | 0–1 | Minimum SL |
| `abandoned_rate_target` | float or None | None | proportion | 0–1 | Abandoned rate target |

## ShrinkageConfig

Agent availability adjustments.

| Parameter | Type | Default | Units | Range | Description |
|---|---|---|---|---|---|
| `rate` | float | required | proportion | 0–1 | Overall shrinkage rate |
| `factors` | dict[str, float] | {} | proportion | — | Shrinkage by category |
| `unplanned_absence_rate` | float | 0.05 | proportion | 0–1 | Unplanned absence |
| `planned_absence_rate` | float | 0.02 | proportion | 0–1 | Planned absence |
| `training_time_percentage` | float | 0.10 | proportion | 0–1 | Training time |
| `meeting_time_percentage` | float | 0.05 | proportion | 0–1 | Meeting time |
| `break_time_percentage` | float | 0.15 | proportion | 0–1 | Break time |

## OccupancyConfig

Agent utilization targets.

| Parameter | Type | Default | Units | Range | Description |
|---|---|---|---|---|---|
| `target` | float | required | proportion | 0–1 | Target occupancy |
| `maximum` | float | 0.95 | proportion | 0–1 | Maximum occupancy |
| `minimum` | float | 0.60 | proportion | 0–1 | Minimum occupancy |
| `calculation_method` | str | "utilization" | — | — | Calculation method |
| `include_break_time` | bool | True | — | — | Include breaks |
| `include_meeting_time` | bool | False | — | — | Include meetings |
| `include_training_time` | bool | True | — | — | Include training |

## SkillConfig

Skill definitions for multi-skill environments.

| Parameter | Type | Default | Description |
|---|---|---|---|
| `skill_id` | str | required | Skill identifier |
| `name` | str | required | Skill name |
| `description` | str or None | None | Description |
| `skill_type` | SkillType | required | voice, email, chat, etc. |
| `channel_type` | ChannelType | required | voice, email, chat, etc. |
| `default_handling_time` | float | required | AHT in seconds |
| `default_appointment_length` | float or None | None | Appointment length (seconds) |
| `required_skills` | list[str] | [] | Prerequisite skills |
| `optional_skills` | list[str] | [] | Optional skills |
| `complexity_level` | int | 1 | 1–10 |
| `priority` | int | 1 | 1–10 (10 highest) |
| `is_active` | bool | True | Whether active |

## Full config example (YAML)

```yaml
name: "production_config"
version: "1.0.0"
description: "Production staffing configuration"

# Interval and timezone
interval_size: 60
interval_unit: "minute"
business_start_hour: 9
business_end_hour: 17
working_days: [1, 2, 3, 4, 5]
timezone: "America/New_York"

# SLA targets
sla_config:
  target: 0.80
  average_speed_of_answer: 20
  acceptable_service_level: 0.90
  minimum_service_level: 0.95

# Shrinkage
shrinkage_config:
  rate: 0.30
  factors:
    unplanned_absence: 0.05
    planned_absence: 0.02
    training: 0.10
    meetings: 0.05
    breaks: 0.15

# Occupancy
occupancy_config:
  target: 0.85
  maximum: 0.95
  minimum: 0.60

# Skills
skills:
  - skill_id: "voice_inbound"
    name: "Inbound Voice"
    skill_type: "voice"
    channel_type: "voice"
    default_handling_time: 180
    is_active: true
```

## Common unit mistakes

**AHT (Average Handle Time):** Must be in seconds. `180` means 3 minutes, not 180 minutes.

**Service level:** Must be a proportion (0.0–1.0), not a percentage. Use `0.80` for 80%, not `80`.

**Shrinkage:** Must be a proportion (0.0–1.0), not a percentage. Use `0.30` for 30%, not `30`.

**Answer threshold:** Must be in seconds. `20` means 20 seconds, not 20 minutes.

**Timezone:** Must be an IANA timezone string (`"America/New_York"`, `"UTC"`, `"Europe/Istanbul"`).

**Interval:** Must be in minutes. `15` means 15-minute intervals, `60` means hourly.

See `wfm_harness/config.py` for the complete, authoritative configuration model.