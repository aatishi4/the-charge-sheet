---
title: Half the cables should still be CCS
description: Ionna opened its first NACS-only sites, the Tesla Semi hit volume production, and Colorado funded 270 fast-charging ports.
date: 2026-10-13
publish: 2026-10-13T09:00:00-05:00
tags: [nacs, networks, fleet, trucks, nevi]
kind: weekly
---

Three things from late September worth your time, and one thing I would do about them.

## 1. Ionna went NACS-only. I wouldn't, yet.

Ionna opened its first fast-charging sites with **no CCS1 cable at all**: two Rechargery Relay locations at Circle K stores in Lancaster and Perris, California, with **4 NACS stalls each**, [reported by State of Charge](https://evchargingstations.com/chargingnews/ionna-first-all-nacs-charging/) on September 22. Ionna's [Perris page](https://www.ionna.com/rechargery/perris-ca-rechargery-circle-k-n-perris-blvd/) lists four NACS connectors at up to **400 kW** for **$0.39 per kWh**. Ionna hasn't said why.

For scale, Paren's [Q2 2026 report](https://www.paren.app/reports/us-ev-fast-charging-q2-2026) had NACS at **22.9% of new non-Tesla fast-charging connectors** installed last quarter. CCS is still **74.6%** of the 48,371-port non-Tesla base.

{{art nacs-vs-ccs | Non-Tesla DC fast-charging connectors. CCS is 74.6% of the 48,371-port installed base. NACS was 22.9% of new connectors installed in Q2 2026. Source: [Paren, Q2 2026](https://www.paren.app/reports/us-ev-fast-charging-q2-2026).}}

**Why it matters:** we're not close to the point where a third-party site should be NACS-only. A lot of non-Tesla EVs on the road still have a CCS port, and those are the drivers a third-party charger lives on. If I'm speccing four DC stalls for a c-store today, at least half the cables are CCS.

We'll get there in a few years, as more models ship with NACS and people trade their CCS cars in. My line is roughly 80% of new vehicles sold with a NACS port, plus Supercharger lines long enough to push Tesla drivers onto third-party chargers. Parts of California may be close. But unless Ionna knows something about who drives past those two Circle Ks, going NACS-only now doesn't make a ton of sense.

## 2. The Tesla Semi is in production. Adoption is the hard part.

Tesla started volume production of the Semi on September 25 at a new plant in Sparks, Nevada, built for **50,000 trucks a year** ([Electrek](https://electrek.co/2026/09/25/tesla-semi-volume-production-launch-nevada-factory/), [TechCrunch](https://techcrunch.com/2026/09/25/tesla-finally-moves-to-electrify-trucking-after-a-decade-of-work-and-delays/)). Loaded to 82,000 pounds it uses about **1.7 kWh per mile**, and it charges at up to **1.2 MW**, enough for 60% of its range in 30 minutes ([The Autopian](https://www.theautopian.com/the-tesla-semi-finally-enters-mass-production-and-charges-with-enough-juice-to-power-a-small-neighborhood/)). Earlier this year Tesla quoted **$260,000** for the 325-mile Standard Range and **$290,000** for the 500-mile Long Range. Tesla's own math puts electricity at **$0.20 to $0.30 a mile**, against about **$0.80** for a diesel truck at 7 mpg.

Some arithmetic for anyone with a depot: at 1.7 kWh a mile, a truck running 300 miles a day needs about **510 kWh** every night. Ten of them need about **5 MWh**.

**Why it matters:** when ZET SCALE ordered 2,500 electric semis, I called it [chicken and egg](/blog/electric-semis-no-chargers/). My answer doesn't change. Production is the chicken now, but adoption is the bigger thing. Tesla producing a truck doesn't mean it gets built at scale, or deployed at scale in time. Trucking is a legacy industry, and new technology that challenges it takes time and a lot of testing before fleets start trading in their diesel trucks. It's a good start. Give it some time.

## 3. Colorado funds 270 more fast-charging ports

Colorado [awarded **$23.2 million**](https://governorsoffice.colorado.gov/news/polis-administration-awards-232-million-fill-gaps-colorados-electric-vehicle-fast-charging) on September 22 for **270 fast-charging ports at 35 locations**, using federal NEVI money and the state's Community Access Enterprise. That's about **$663,000 per site**, or roughly **$86,000 per port**. The state says it adds **16%** to a network of more than 1,680 ports.

The winners range from Tesla, Electrify America, EVgo and Blink to 7-Eleven, Love's, Phillips 66 and regional operators like Helios and Red E ([KRDO](https://krdo.com/news/2026/09/22/colorado-awards-ev-fast-charging-grants/)). Projects have two years to finish.

## What I'd do

If you're speccing DC chargers for a site today, keep at least half the cables CCS. Revisit that when NACS is on roughly 80% of new EVs sold, or when Tesla drivers start showing up because the Supercharger down the road has a line. Until then, a NACS-only site turns away the drivers third-party charging depends on.

The [buying guide](/buying-ev-chargers/) covers hardware and connector choices, and the [site selection guide](/ev-charging-site-selection/) helps you figure out who actually drives past your lot. For depots, the [fleet charging guide](/fleet-ev-charging/) and [fleet charging calculator](/fleet-charging-calculator/) take your own numbers. If you're chasing grant money, start with the [financing guide](/ev-charging-station-financing/).
