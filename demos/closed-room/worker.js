// Closed Room inference worker.
// Runs speech-to-text (Whisper) and the optional summary model entirely in
// this browser tab. Audio and text are passed in by postMessage and never
// sent over the network. The only network traffic is the one-time download
// of the library and model weights, which the browser then caches.

import {
  pipeline,
  env,
  TextStreamer,
} from "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.8.1/dist/transformers.min.js";

env.allowLocalModels = false;
env.useBrowserCache = true;

// Report every network request this worker makes to the page's ledger.
try {
  new PerformanceObserver((list) => {
    for (const en of list.getEntries()) {
      self.postMessage({ type: "net", url: en.name, bytes: en.transferSize || 0, from: "worker" });
    }
  }).observe({ type: "resource", buffered: true });
} catch {}

let asr = null;
let asrKey = "";
let llm = null;
let llmKey = "";

async function hasWebGPU() {
  try {
    if (!self.navigator || !navigator.gpu) return false;
    const a = await navigator.gpu.requestAdapter();
    return !!a;
  } catch {
    return false;
  }
}

function progressRelay(kind) {
  const files = new Map();
  return (p) => {
    if (p.status === "progress" || p.status === "download" || p.status === "done") {
      const f = files.get(p.file) || { loaded: 0, total: 0 };
      if (p.loaded != null) f.loaded = p.loaded;
      if (p.total != null) f.total = p.total;
      if (p.status === "done" && f.total) f.loaded = f.total;
      files.set(p.file, f);
      let loaded = 0,
        total = 0;
      for (const v of files.values()) {
        loaded += v.loaded;
        total += v.total;
      }
      self.postMessage({ type: "progress", kind, loaded, total, file: p.file });
    }
  };
}

async function loadAsr(model, wantGpu) {
  const gpu = wantGpu && (await hasWebGPU());
  const key = model + (gpu ? "@gpu" : "@wasm");
  if (asr && asrKey === key) return gpu;
  if (asr && asr.dispose) await asr.dispose();
  asr = null;
  self.postMessage({ type: "status", kind: "asr", text: "Loading speech model" });
  asr = await pipeline("automatic-speech-recognition", model, {
    device: gpu ? "webgpu" : "wasm",
    dtype: gpu
      ? { encoder_model: "fp32", decoder_model_merged: "q4" }
      : { encoder_model: "q8", decoder_model_merged: "q8" },
    progress_callback: progressRelay("asr"),
  });
  asrKey = key;
  // Warm up so the first real chunk is not slow.
  await asr(new Float32Array(16000));
  return gpu;
}

async function loadLlm(model) {
  if (!(await hasWebGPU())) throw new Error("Summaries need WebGPU (current Chrome, Edge or Safari 26).");
  if (llm && llmKey === model) return;
  self.postMessage({ type: "status", kind: "llm", text: "Loading summary model" });
  llm = await pipeline("text-generation", model, {
    device: "webgpu",
    dtype: "q4f16",
    progress_callback: progressRelay("llm"),
  });
  llmKey = model;
}

self.onmessage = async (e) => {
  const m = e.data;
  try {
    if (m.type === "load-asr") {
      const gpu = await loadAsr(m.model, m.gpu);
      self.postMessage({ type: "ready", kind: "asr", device: gpu ? "WebGPU" : "CPU (WebAssembly)" });
    } else if (m.type === "transcribe") {
      if (!asr) throw new Error("Speech model is not loaded.");
      const t0 = performance.now();
      const out = await asr(m.audio, {
        chunk_length_s: 30,
        stride_length_s: 5,
      });
      const text = (out.text || "").trim();
      self.postMessage({
        type: "segment",
        id: m.id,
        start: m.start,
        end: m.end,
        text,
        ms: Math.round(performance.now() - t0),
      });
    } else if (m.type === "load-llm") {
      await loadLlm(m.model);
      self.postMessage({ type: "ready", kind: "llm", device: "WebGPU" });
    } else if (m.type === "summarize") {
      await loadLlm(m.model);
      const messages = [
        {
          role: "system",
          content:
            "You write concise, accurate meeting notes for a lawyer. Use only facts stated in the transcript. Never invent names, dates, amounts or advice. If something is unclear, say so.",
        },
        {
          role: "user",
          content:
            `Matter: ${m.matter || "(not given)"}\n\nTranscript:\n${m.transcript}\n\n` +
            "Write notes with these headings:\nSummary (3-5 sentences)\nKey facts\nAdvice given or discussed\nAction items (who, what, when)\nOpen questions",
        },
      ];
      let acc = "";
      const streamer = new TextStreamer(llm.tokenizer, {
        skip_prompt: true,
        skip_special_tokens: true,
        callback_function: (t) => {
          acc += t;
          self.postMessage({ type: "summary-token", text: acc });
        },
      });
      await llm(messages, { max_new_tokens: 700, do_sample: false, streamer });
      self.postMessage({ type: "summary-done", text: acc.trim() });
    }
  } catch (err) {
    self.postMessage({ type: "error", kind: m.type, message: String(err && err.message ? err.message : err) });
  }
};
