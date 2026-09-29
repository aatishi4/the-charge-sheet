---
title: Uptime says the charger is online. It doesn't say it works.
description: A site can report great uptime and still send drivers away. The number that matters is whether the first charge attempt works.
date: 2026-10-29
publish: 2026-10-29T09:00:00-05:00
tags: [reliability, uptime, operations]
kind: essay
---

Federal rules say a NEVI-funded charging port has to average more than [**97% uptime**](https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-680/section-680.116) over a year. Plenty of sites clear that. And J.D. Power's 2026 public charging study still found that [**12% of visits**](https://www.jdpower.com/business/press-releases/2026-u-s-electric-vehicle-experience-evx-public-charging-study/) ended without a charge.

Both numbers can be true at the same time, because they measure different things. Uptime doesn't tell you whether a site is good. It tells you whether the charger is online.

## What uptime actually measures

Uptime means the charger is reporting. It's connected to the internet, and the network can see it and show it as ready to charge. That's the charger's opinion of itself.

The federal formula also leaves some things out. Outages caused by the utility, scheduled maintenance, vandalism, natural disasters, and failures that are the vehicle's fault can all be [excluded from the count](https://www.ecfr.gov/current/title-23/chapter-I/subchapter-G/part-680/section-680.116). Some of those exclusions are fair. None of them help the driver standing at the plug.

## Where sessions actually break

The break almost always happens in the workflow: the handoffs between the payment terminal, the network software and the charger. Something in between doesn't go through.

A few ways it goes wrong, every one of them while the charger reports that it's up:

- **The authorization never arrives.** The card reader asks the network for approval, and the message gets lost between the point of sale, the charging management system and the charger.
- **The pre-authorization is too high.** The driver's card only has so much available, the hold the site asks for is bigger than that, and the payment doesn't clear.
- **The car gives up waiting.** A driver at a new site opens the charge port, then downloads the app, reads the instructions and figures out the screen. By the time they plug in, the port has timed out. They did everything else right, and it still doesn't charge.

That last one isn't the charger's fault or the network's. It's people not knowing how their cars work, which is normal. It still counts as a failed visit to the driver, and they'll remember your address.

{{art session-chain | Illustrative. Uptime sees whether the charger is online. A session also has to clear the card, the network's approval and the car's handshake, and any of those can fail while the charger reports ready.}}

## Measure what the driver sees

Uptime is one piece of the puzzle. The number I'd rather see is charge success rate, and especially first-time charge success: of the drivers who walked up and tried, how many got a charge on the first attempt?

That number catches the payment problems, the network problems and the timed-out ports that uptime never sees. Paren's reliability score already goes that way. It [counts successful sessions, retries and failed attempts](https://www.paren.app/reports/us-ev-fast-charging-q2-2026) along with downtime, and most states land in the low to mid 90s.

If I'm honest, I think anything above 80% first-time success is good.

## What to ask for

If you own a site, or you're about to sign with a network to run one:

- Ask for session success rate and first-time success rate, not just uptime.
- Ask for the failed sessions broken out by cause: payment declined, authorization timed out, vehicle fault, charger fault.
- Ask what the pre-authorization hold is, and whether it can be set lower.
- Put the instructions where a new driver will read them before opening the charge port.

A charger that's online and doesn't charge is a broken charger with a good report.

The [connectivity guide](/ev-charger-connectivity/) covers the communication side, where a lot of these failures start. The [buying guide](/buying-ev-chargers/) has a chart of what the uptime report says versus what drivers experienced over thirty days, and the [benchmarks](/ev-charging-benchmarks/) show what real sites look like.
