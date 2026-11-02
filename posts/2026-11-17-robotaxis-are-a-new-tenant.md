---
title: Robotaxis are a new kind of tenant. Price them like real estate.
description: Waymos are filling public fast chargers, California redefines what "up" means, and Blink renames itself Blink Energy.
date: 2026-11-17
publish: 2026-11-17T07:00:00-06:00
tags: [robotaxis, fleet, pricing, reliability, uptime, networks]
kind: weekly
---

Three things from late October worth your time, and one thing I would do about them.

## 1. Robotaxis are a new kind of tenant

The [Los Angeles Times](https://www.yahoo.com/news/us/articles/come-droves-robotaxis-hogging-ev-130237419.html) reported on October 30 that Waymo robotaxis are filling public fast chargers in San Diego. One driver told the Times he waited **an hour** and described three Waymos at a station with four spots. EVgo says its San Diego stations are open to everyone, robotaxis included, and it had **120 stalls** set aside for AV companies earlier this year. The city says autonomous vehicles pay the same fees as anyone else. Waymo says it staffs some public sites, tries not to bunch up, and builds its own charging as a market matures. Drivers have made the same complaint in [Las Vegas](https://www.ktnv.com/news/local-ev-drivers-say-waymo-robotaxis-hogging-public-charging-stations), Nashville and St. Louis ([InsideEVs](https://insideevs.com/news/813929/waymo-ev-charging-problem-california/)).

**Why it matters:** robotaxis are a new tenant class, and it doesn't really exist yet. They aren't a traditional fleet. A delivery fleet needs warehouse space and not as much infrastructure. They aren't a taxi company either, which needs a repair shop and driver facilities. A robotaxi needs to be in an urban environment so it can reach riders, and it needs a heavy dose of charging.

So how do you price them? I wouldn't price them any differently from the guy camped at the Starbucks table. Real estate is real estate, and the price should depend on demand. Start with how real estate is priced in that area, then adjust and modulate based on market demand.

The bigger point is for landlords. If they want to keep up, charging has to be baked into the underlying asset. That gives fleets in general a foothold for the future, so it future-proofs both sides. That could even carry a premium. It depends on how the infrastructure gets built out.

## 2. California says "up" means it charged. That's a start.

California's charger reliability rules are [finally in place](https://www.canarymedia.com/articles/ev-charging/california-ev-charging-reliable). Publicly or ratepayer-funded DC fast chargers installed since January 2024 must hit **97% uptime per port** for **six years**. A port counts as up only when its hardware and software are online, it's available, and it [successfully dispenses electricity](https://www.energy.ca.gov/programs-and-topics/programs/clean-transportation-program/ev-charger-data-and-reliability-1). Vandalism (up to 10 days per incident), grid outages, natural disasters and up to **72 hours** a year of planned maintenance don't count against it. New DC chargers installed after September 27 must run OCPP 2.0.1 and send the state hourly data. Older ones report twice a year, and the first report is due January 31. One network employee told Canary the rules are an onerous data-reporting exercise.

{{art what-counts-as-up | Illustrative. California counts a port as up when it is online, available and dispenses electricity, and requires 97% per-port uptime for six years. The definition on the CEC's page doesn't say how much power counts, so a 150 kW port delivering 75 kW or 40 kW still dispensed electricity. Source: [California Energy Commission](https://www.energy.ca.gov/programs-and-topics/programs/clean-transportation-program/ev-charger-data-and-reliability-1).}}

**Why it matters:** this is a good way to start working toward a practical solution. It doesn't solve the problem right away. Delivering a charge is supposed to mean the charger works, but how much charge? What type? Is it charging at full capacity or at 50% of its rating? If it isn't dispensing, is that a grid limitation, a power reduction, a failed module, or the vehicle?

Enforcement is its own challenge. Unless you can see the OCPP logs in real time, and most people can't, this is a good solution on paper. You can run an application, and the charger still doesn't work.

What needs to happen is integration between the major networks' back ends and public repositories that report whether each port is dispensing, every 24 hours or even every hour. The data costs about the same either way. Hourly data gives a lot more visibility. Tesla does a really good job of this. It tells drivers and Google Maps when stalls are live and when they aren't. Take that model and put it on an open source platform. That takes cooperation, integration and some tech build-out, and it may or may not happen in the time we need it to.

I wrote about why uptime and a working charge aren't the same thing in [Uptime says the charger is online](/blog/uptime-is-not-success/).

## 3. Blink Charging becomes Blink Energy

Blink said on October 29 that it plans to rename itself Blink Energy and add energy management and battery storage to charging. The next day it filed an [S-3](https://www.sec.gov/Archives/edgar/data/1429764/000149315226049471/forms-3.htm) with an at-the-market program to sell up to **$100 million** of stock. The filing lists the last sale price at **$0.41** and **145.2 million** shares outstanding, which works out to about **$60 million** of market value. Blink's load-management software runs at **52** of its own DC fast-charging sites, and 26 of them actively use it. One cut its billed peak demand **23%** in its first month ([EV Fleet World](https://evfleetworld.co.uk/blink-charging-pivots-to-blink-energy-to-drive-battery-storage-and-energy-management-expansion/)). Its third-quarter results were scheduled for November 5.

## What I'd do

If you own property in a dense part of town, price charging the way you'd price the real estate under it, and adjust to demand from there. Then build the charging into the building itself. Robotaxis are the first tenant to need it at that scale, and they won't be the last.

For fleets and depots, start with the [fleet charging guide](/fleet-ev-charging/) and the [fleet charging calculator](/fleet-charging-calculator/). For where a site makes sense, see [site selection](/ev-charging-site-selection/). The [connectivity guide](/ev-charger-connectivity/) covers the OCPP side of reliability, and the [battery storage guide](/battery-storage-ev-charging/) covers what storage can and can't do about a demand charge.
