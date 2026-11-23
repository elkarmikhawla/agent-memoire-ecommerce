# E-commerce agent memory (Relate by Neo4j)

Memory for an AI operations agent that helps a small online seller (Shopify + WhatsApp / Instagram / Telegram) after an order is placed: confirmations, order changes, and recognising the same customer across channels, with the seller keeping control.

> Work in progress for the Relate by Neo4j Hackathon 2026. All data in this repo is fictional.

## Why a graph

The hard part is not storing orders, it is knowing **who is who**: one phone number shared by a family, two customers with the same name, the same person writing from another channel. A graph keeps these links explicit so the agent can say "I'm not sure" instead of guessing.

## How Relate is used

- **Mode: single file** (`memoire.rl`), so judges can open and inspect the store directly from the repo.
- Embedded in Python (`import relate`), no server.

## Run it

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python donnees_fictives.py
```

This loads fictional customers, products and orders into `memoire.rl` and prints checks: the same number written three ways, a family sharing one number, two homonyms, and a duplicate order.
