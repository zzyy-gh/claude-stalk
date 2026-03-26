# GTC 2026 -- The Inference Kingdom Expands

## Overview

At GTC 2026, Nvidia announced three entirely new systems: Groq LPX, Vera ETL256, and STX, alongside updates to Kyber rack architecture and CPO networking roadmap. The company continues aggressive innovation in AI infrastructure, particularly for inference workloads.

## Groq LPU Architecture

The Groq LPU represents a specialized design fundamentally different from GPUs. Rather than general-purpose cores, it organizes "functional units into groups called slices" that handle vector operations, memory, tensor manipulation, and matrix multiplication. Data streams horizontally while instructions flow vertically--resembling a systolic array architecture.

### LP30 Specifications

The LP30 (Groq's third-generation LPU) features:
- 500MB on-chip SRAM
- 1.2 PFLOPS FP8 compute capability
- Manufacturing on Samsung's SF4X process node
- Monolithic die design without advanced packaging requirements

This represents substantial SRAM density--crucial for low-latency inference--but comparatively modest compute versus GPU alternatives.

## Attention FFN Disaggregation (AFD)

Nvidia integrates LPUs through a novel approach splitting transformer operations by workload characteristics:

**Attention operations** map to GPUs, which handle dynamic KV cache loading patterns efficiently with substantial HBM capacity. **FFN (Feed-Forward Network) operations** map to LPUs, exploiting their deterministic architecture and high SRAM bandwidth for stateless computations.

This disaggregation maximizes both latency optimization and throughput by leveraging each architecture's strengths.

## LPX Rack System

Each compute tray contains:
- 16 LP30 modules (belly-to-belly mounting for density)
- 2 Altera FPGAs ("Fabric Expansion Logic")
- 1 Intel Granite Rapids CPU
- BlueField-4 front-end module

The FPGAs convert Groq's C2C protocol to Ethernet for scale-out fabric connectivity, and to PCIe for CPU communication. They also provide up to 256GB DDR5 memory for KV cache offloading.

### Networking Bandwidth

Within-rack C2C scale-up achieves "640TB/s of scale up bandwidth per rack" through 256 LPUs x 90 lanes x 112Gbps configuration.

## CPO Roadmap

Nvidia's Coherent Pluggable Optics deployment strategy prioritizes copper interconnects where feasible:

**Rubin Generation:**
- NVL72 Oberon: All-copper scale-up
- NVL576 (8 Oberon racks): Copper within racks, CPO between racks for two-tier all-to-all topology

**Feynman Generation:**
- NVL1152 (8 Kyber racks): Copper within racks, CPO for inter-rack connections

## Kyber Rack Updates

Densification continues with 4x Rubin Ultra GPUs and 2x Vera CPUs per compute blade, totaling 144 GPUs per rack across 36 blades. The system features:
- 72 NVLink 7 switches per rack
- 28.8Tbit/s aggregate bandwidth per switch
- Copper flyover cables connecting switches to midplane

## Vera ETL256 CPU Rack

A dedicated CPU rack addresses growing infrastructure needs beyond GPU compute. The system packs "256 CPUs into a single rack" using liquid cooling, maintaining copper-only interconnects within 32 compute trays arranged around four central switch trays.

This addresses CPU bottlenecks in reinforcement learning, simulation, and data preprocessing workloads.

## CMX and STX Storage Architecture

**CMX** (Context Memory Storage) extends the memory hierarchy with NVMe tier for KV cache offloading, using BlueField DPU NICs for acceleration.

**STX** provides a reference storage rack architecture with:
- 32 Vera CPUs
- 64 CX-9 NICs
- Support from major storage vendors (NetApp, DDN, Dell, HPE, and others)

This standardizes storage integration across inference clusters.

## Key Takeaways

Nvidia's 2026 roadmap emphasizes heterogeneous compute--combining specialized LPUs for latency-sensitive decode operations with GPUs for throughput-intensive prefill. The company systematically expands from compute through networking to storage layers, establishing comprehensive infrastructure standards for hyperscale inference deployments.
