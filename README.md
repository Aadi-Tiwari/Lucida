# Lucida

Explore how lesson structure might affect a synthetic classroom, with a browser demonstration and separate Python services for parsing and simulation.

## Choose a path

| Path | What it actually runs |
| --- | --- |
| Browser demo (`index.html`) | Sentence splitting, heuristic concepts, randomized personality traces, and templated suggestions |
| Parsing API (`main.py`) | Groq concept extraction, local sentence embeddings, and synthetic student generation |
| Simulation API (`person_b/socraticsem-main/`) | Numerical simulation and analysis of a supplied handoff; its `/simulate` endpoint currently uses mock parsing |

The browser demo does not call the Python analysis services. Its scores are illustrative, not measured student outcomes or validated dropout predictions. It shows a representative trace for each personality rather than simulating every displayed student independently.

## Browser demo

Text and document input need no configuration file. Serve the root:

```sh
python -m http.server 8080 --bind 127.0.0.1
```

Open <http://127.0.0.1:8080>. Paste a lesson or upload a text document. Charting and document readers load from public CDNs. Image text extraction is not implemented.

For optional local audio transcription, copy `config.example.js` to the ignored `config.js`, configure your Groq key, and open `http://127.0.0.1:8080/?config=local`. Only loopback pages load that explicitly requested configuration. The key is visible to your browser. Do not publish it or use this path as a shared hosted service. A hosted transcription feature needs a server-side credential boundary.

The Vercel configuration publishes the static browser demo, not the Python ML service. `node scripts/build-static.mjs` copies the page into `dist/` and writes an empty public configuration. It never copies your private `config.js`. The Python service remains a separate local application; its model dependencies exceed a serverless function bundle.

## Parsing API

Use Python 3.11:

```sh
python -m venv .venv
```

Activate the environment, then install and start:

```sh
python -m pip install -r requirements-dev.txt
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Set `GROQ_API_KEY` in the process environment before starting. This API does not automatically load `.env`. `GET /health` checks the process. `POST /parse-lesson` accepts:

```json
{"text": "Mass is the amount of matter in an object.", "num_students": 100}
```

The response contains `chunks`, `students`, and `personality_modifiers`. Chunks include sequential order, concepts, prerequisites, and embedding vectors. The embedding model is downloaded on first use. Blank lessons and student counts outside the interface bounds are rejected.

## Simulation API

Install `person_b/socraticsem-main/requirements.txt` in an environment, change to that directory, and run:

```sh
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

Send the parsing API's handoff to `POST /simulate/chunks-only`. The separate `POST /simulate` endpoint accepts `lesson_text` and `n_students`, but generates mock concept vectors. Optional rewrite suggestions use `GROQ_API_KEY` from the process environment. Without a key, the response identifies template suggestions with `suggestion_source: "template"`. Neither endpoint establishes predictive validity for real classrooms.

## Checks

Simulation handoffs must contain arrays of chunk and student objects with nonempty, finite vectors of a consistent dimension. Invalid handoffs return a client error instead of silently producing scores from malformed vectors.

With the root virtual environment active:

```sh
python -m pytest -q
```

The tests validate lesson input, provider-response structure, embedding shape, and the parser-to-simulator handoff without calling Groq. Live provider behavior, model downloads, and educational validity need separate evaluation.

Run the browser-script syntax and lesson-bridge regression checks with Node:

```sh
node --test tests/browser.test.mjs
```

## License

Original project source is available under the [MIT License](LICENSE). Third-party dependencies, model weights, fonts, documents, and datasets retain their own licenses. This license does not grant rights to third-party assets.
