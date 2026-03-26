# Web Digest -- 2026-03-26 13:11 MPST

## Overview

7 new articles found across 7 of 10 monitored sources. 3 sources could not be reached (Stratechery: no RSS feed found; Linas's Newsletter and Simon Wilson's Newsletter: feed parsing errors).

**What happened:** Nvidia unveiled a heterogeneous compute strategy at GTC 2026, pairing GPUs with Groq LPUs for disaggregated inference while extending its infrastructure stack to storage and dedicated CPU racks. The semiconductor supply chain remained under pressure from multiple directions -- a $2.5B chip smuggling case exposed export control vulnerabilities, memory stocks sold off on misunderstood compression research, and Arm signaled a strategic shift from IP licensing toward system-level chip platforms. On the AI model side, OpenAI is cutting consumer apps (Sora) to focus on enterprise and AGI deployment ahead of its IPO, while Nathan Lambert argued that AI self-improvement will be "lossy" rather than exponential.

**What to watch:** Nvidia's Attention FFN Disaggregation architecture could reshape inference infrastructure economics if LPU integration delivers on latency promises -- though real-world performance data beyond Nvidia's own benchmarks is not yet available. Arm's downstream push risks ecosystem trust erosion with customers who may see a future competitor. The agentic computing wave is reportedly driving revenue inflections at CDN and infrastructure providers, though the "B2A" vertical thesis originates from a single paywalled Citrini piece and the specific CDN revenue claims were not independently verified in public filings.

## Articles

### [$2.5 Billion in Smuggled Chips, Uber's Rivian Partnership, Trustpilot AI Use Surges](https://contraryresearch.substack.com/p/25-billion-in-smuggled-chips-ubers)
**Source**: [Contrary Research](https://contraryresearch.substack.com) | **Published**: 2026-03-21 12:03 | **People**: Yih-Shyan Liaw

Three individuals connected to Super Micro Computer, including co-founder Yih-Shyan Liaw, were charged with smuggling $2.5 billion worth of advanced NVIDIA chips to China through Southeast Asian intermediaries using falsified paperwork. The case underscores the fundamental tension in US export control policy -- significant demand motivates circumvention, and the primary effect may be enriching intermediaries rather than meaningfully slowing Chinese AI advancement. Separately, Uber signed a $1.25 billion deal with Rivian for robotaxis targeting 2028 deployment, though Rivian has yet to begin R2 production or deploy an autonomous driving system. Trustpilot emerged as the fifth-most cited domain by language models, with LLM-driven click-throughs up 1,490% YoY _(single-source metric from Trustpilot's own reporting)_, as its open data strategy and e-commerce focus gave it a structural advantage over Yelp and Google Reviews in the AI era. The platform's annual profit nearly quadrupled in 2025.

### [Agentic Utilities](https://citriniresearch.com/p/agentic-utilities)
**Source**: [Citrini](https://www.citriniresearch.com) | **Published**: 2026-03-25 12:36 | **People**: Jensen Huang

Citrini frames the current AI moment as the "Agentic Era" -- the third phase of AI adoption following infrastructure hyperscaling and democratization. The catalyst was OpenClaw, an open-sourced agentic library that enabled AI to shift from reactive chatbots to autonomous task handlers running overnight. The piece identifies three investment winner categories: infrastructure (CDN providers like Cloudflare and Akamai showing revenue inflections from agentic traffic), ecosystem (a new "B2A" vertical for payment rails, stablecoins, and agentic wallets enabling non-human financial transactions), and governance (observability and counter-AI solutions for rogue agent protection). Jensen Huang's suggestion that engineers should consume $250K in annual tokens highlights the computational intensity of agentic workloads. The full analysis is behind a paywall. _(paywalled -- Summary based on free preview; detailed analysis of specific stocks and theses behind paywall.)_

### [The memory sector has plummeted, what is the market panicking about?](https://globalsemiresearch.substack.com/p/the-memory-sector-has-plummeted-what)
**Source**: [Global Semi Research](https://globalsemiresearch.substack.com) | **Published**: 2026-03-26 04:30 | **People**: --

Memory chip stocks (Micron, SK Hynix, Samsung, Kioxia) sold off sharply on fears that Google's TurboQuant compression algorithm could reduce memory requirements by 6x. The article debunks the panic on three grounds: the paper is from April 2025, the 6x compression applies only to KV cache during inference (not model weights or training), higher compression ratios increase decompression latency which is unacceptable for inference scenarios, and historically efficiency gains expand total demand via Jevons Paradox rather than reducing it. The piece argues the selloff is irrational and that longer context windows and larger batch sizes enabled by compression will ultimately increase overall memory requirements.

### [Lossy self-improvement](https://www.interconnects.ai/p/lossy-self-improvement)
**Source**: [Interconnect by Nathan Lambert](https://www.interconnects.ai) | **Published**: 2026-03-22 19:39 | **People**: Nathan Lambert

Nathan Lambert challenges the "fast takeoff" narrative by proposing "lossy self-improvement" (LSI) as a more realistic model for AI progress -- where friction and inefficiencies prevent truly exponential recursive self-improvement. He identifies three core frictions: automatable AI research is too narrow (optimizing test loss differs from balancing the multiple objectives that drive real breakthroughs), parallel agents hit Amdahl's law diminishing returns when human supervision becomes the bottleneck, and organizational politics around compute allocation impose constraints automation cannot remove. Lambert argues models excel at "hill climbing" but struggle with paradigm shifts needed for continual learning and post-scaling innovations. His conclusion: AI progress will look "more linear than exponential" in retrospect, and the industry will remain in lossy self-improvement for several years.

### [Nvidia -- The Inference Kingdom Expands](https://newsletter.semianalysis.com/p/nvidia-the-inference-kingdom-expands)
**Source**: [Semianalysis](https://newsletter.semianalysis.com) | **Published**: 2026-03-24 00:27 | **People**: --

Semianalysis provides deep technical coverage of Nvidia's GTC 2026 announcements, centered on three new systems: Groq LPX, Vera ETL256, and STX. The marquee development is Attention FFN Disaggregation (AFD), which splits transformer operations between GPUs (for attention with dynamic KV cache) and Groq LPUs (for deterministic FFN computations), maximizing both latency and throughput. The LP30 LPU features 500MB on-chip SRAM and 1.2 PFLOPS FP8 on Samsung SF4X. Nvidia's CPO roadmap prioritizes copper where feasible -- Rubin NVL72 is all-copper, with CPO reserved for inter-rack connections at NVL576+ scale. Kyber racks now pack 144 GPUs across 36 blades with 72 NVLink 7 switches. A dedicated Vera ETL256 CPU rack addresses bottlenecks in RL, simulation, and preprocessing. The overall strategy is heterogeneous compute with comprehensive infrastructure standards spanning compute, networking, and storage layers for hyperscale inference.

### [Arm Is No Longer Just Selling IP -- It is Stepping In to Build Chips Now](https://tspasemiconductor.substack.com/p/arm-is-no-longer-just-selling-ip)
**Source**: [Semivision](https://tspasemiconductor.substack.com) | **Published**: 2026-03-25 05:43 | **People**: Rene Haas

Semivision analyzes Arm's strategic evolution from pure IP licensor toward a "system-level platform player," highlighted by its AGI CPU initiative and Compute Subsystems offering. CEO Rene Haas argues CPUs are being redefined as orchestration cores for agentic AI workflows that require dozens of intermediate steps -- intent understanding, API calls, result aggregation, and retry logic -- beyond what accelerators handle alone. The piece identifies a key tension: Arm's historical strength derived from ecosystem neutrality, and moving downstream toward chip productization risks eroding trust among customers who may see a future competitor. SoftBank's acquisition strategy positions Arm centrally in infrastructure shifts rather than optimizing for stable licensing cash flows. Meta's endorsement provides credibility, but universal hyperscaler adoption remains uncertain given divergent priorities around cost, software maturity, and supply control.

### [AI: OpenAI trims AI Applications down to 'AGI' basics. RTZ #1037](https://michaelparekh.substack.com/p/ai-openai-trims-ai-applications-down)
**Source**: [Michael Parekh](https://michaelparekh.substack.com) | **Published**: 2026-03-26 05:02 | **People**: Sam Altman, Fidji Simo

OpenAI is shutting down Sora to concentrate resources on core AI models and enterprise solutions ahead of its anticipated IPO. The video app reportedly cost ~$5B annually while generating under $500K monthly in revenue _(reportedly -- figures sourced from industry estimates, not OpenAI disclosures)_, with only $2.1M in lifetime in-app purchases. Fidji Simo's title shift from "CEO of Applications" to "AGI Deployment" signals strategic reorientation. OpenAI has completed initial development of its next model codenamed "Spud." The moves reflect intensifying competition with Anthropic for enterprise customers and investor attention, with both companies approaching blockbuster IPOs. Walt Disney abandoned a planned $1B Sora-related investment _(single-source -- not independently confirmed)_, while the Sora research team pivots to "world simulation research" for robotics.

## No new content

- [Stratechery - Ben Thompson](https://stratechery.com) _(no RSS feed found)_
- [Linas's Newsletter](https://linas.substack.com) _(feed parsing error)_
- [Simon Wilson's Newsletter](https://simonw.substack.com) _(feed parsing error)_
