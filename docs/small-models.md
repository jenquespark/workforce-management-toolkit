# Language Model Integration

The Toolkit is designed so that language models — including small local ones — can use WFM capabilities without reimplementing the mathematics themselves.

## Design boundary

Core principle: **calculations are delegated to explicit software providers rather than performed by an LLM.**

If a language model is used at all, it handles:

- Interpreting what the user wants
- Discovering which capability matches (via the capability registry)
- Gathering the required parameters
- Explaining the result

The provider libraries (StatsForecast, pyworkforce, Pandera) execute the actual forecasting, staffing, and validation. The model never produces the numbers itself.

## Why this boundary exists

Language models are not reliable at WFM mathematics. They can hallucinate formulas, miscalculate Erlang C, confuse service level definitions, or produce plausible-looking but incorrect numbers. Routing the calculation to an explicit provider eliminates that failure mode.

## How it works

1. **Discovery:** The model reads the capability registry to find what operations exist and what inputs they require.
2. **Parameter gathering:** The model collects the required parameters (arrival rate, AHT, service level target, etc.).
3. **Execution:** The Toolkit calls the provider library with those parameters.
4. **Explanation:** The model interprets the structured result for the user.

For example, a user asks "how many agents do I need for 150 calls/hour with 180s AHT at 80% service level?" The model identifies the staffing capability, passes the parameters to the pyworkforce adapter, and the adapter performs the Erlang C calculation. The model then explains the result.

## Applicability

Any language model with basic tool-use capability can follow this pattern. The Toolkit also works entirely without a model — the Python API and automation scripts do not require one.

Language model integration is a secondary convenience, not a core requirement. The Toolkit's value stands on its own: consistent interfaces, explicit units, machine-readable capability descriptions, and honest provider availability reporting.