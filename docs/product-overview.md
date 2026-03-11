# Travel Negotiation Copilot: Simple Product Overview

## What is this product?

Travel Negotiation Copilot is an AI-assisted planning tool for sports team travel operations.

It helps an operations team plan road trips faster by turning schedule data, team rules, vendor preferences, and past travel patterns into a first draft of:

- a travel recommendation
- hotel and charter outreach drafts
- a master itinerary
- a risk log for the trip

The product is not designed to replace the operations team. It is built to help them do their work faster, with better structure and less manual effort.

## Why was this product built?

Sports travel planning is usually very manual.

Operations teams often need to:

- review the game schedule
- calculate travel windows
- check team policies
- compare hotels and charter options
- draft outreach emails
- build a final itinerary packet

That process takes time and usually depends on a small number of experienced staff.

This product was built to reduce that workload and give teams a faster way to create a strong first draft. The goal is to save planning time, improve consistency, and make it easier to spot risks before outreach starts.

## What exists in the POC today?

The current proof of concept is a simple Streamlit app for one fictional basketball team and one demo trip scenario.

Right now, the POC can:

- load a seeded 3-city domestic road trip scenario
- break the schedule into travel legs and timing windows
- apply team policy rules such as hotel limits, aircraft preference, curfew, and recovery windows
- rank hotel and charter vendors using transparent scoring logic
- use past trip notes, policy text, and templates as grounding context
- generate a recommendation, itinerary draft, negotiation summary, and outreach emails
- use a live OpenAI model when credentials are available
- fall back to a deterministic draft when no model key is present
- require human approval before export
- export the final packet as Markdown or HTML
- let the operator change variables like party size or curfew and regenerate outputs quickly

## What can be added next?

This POC is intentionally narrow. A product version could grow in several useful ways.

Possible next additions:

- upload real schedule CSV and PDF files
- upload team policy documents and vendor lists
- support quote entry and quote comparison inside the app
- track negotiation rounds and hold deadlines
- add practice facility, bus, and catering vendors
- support multiple teams and leagues
- add approval roles for finance, team operations, and executives
- connect with email systems so drafts can be reviewed and sent from one place
- add savings tracking against historical trip costs
- add dashboards for turnaround time, compliance, and vendor performance
- support a stronger retrieval layer with embeddings or a vector database

## Why is this type of product less available in the market?

There are a few reasons.

First, this is a niche workflow. Team travel operations is a specialized job, and many software companies focus on larger markets like general corporate travel or hotel booking.

Second, the work is not only about booking. It includes team rules, recovery needs, charter timing, room mix, approvals, relationships with preferred vendors, and many last-minute changes. That makes the workflow more complex than a normal travel app.

Third, the data is often hard to collect in one place. A team may have schedules in one format, policies in documents, vendor notes in email threads, and historical knowledge in spreadsheets or staff memory.

Fourth, buyers in this space care about control and trust. They usually do not want a system that sends messages or makes commitments automatically. They want decision support, review, and approval.

Because of those reasons, the market has fewer polished products focused specifically on AI-driven sports travel negotiation. That creates an opportunity for a tool that is specialized, human-in-the-loop, and built around real operations workflows.

## Simple product value

In simple terms, this product helps a team say:

"Give me a strong first draft for this road trip, show me the best options, explain the risks, and let me approve everything before anything goes out."

That is the core value of the current POC and the main reason it can become a useful product.
